import asyncio
import logging
from config_loader import load_config
from modules.utils import retry, ensure_paper_trading_symbol
from modules.orders import init_exchange, place_order, calculate_position_size, fetch_balance
from modules.indicators import calculate_indicators, detect_fvg
import pandas as pd


def setup_logger() -> logging.Logger:
    """
    Set up and return a logger for the tradingbot.
    """
    logger = logging.getLogger("tradingbot")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


@retry(max_attempts=3, initial_delay=1.0)
async def main() -> None:
    """
    Main async entrypoint for the tradingbot with risk sizing, SL/TP OCO orders.
    """
    log = setup_logger()
    cfg = load_config()

    # Initialize exchange
    exchange = init_exchange(
        api_key=cfg.API_KEY,
        api_secret=cfg.API_SECRET,
        exchange_name=cfg.EXCHANGE
    )
    log.info("Tradingbot startad med OCO SL/TP-logik.")

    # Fetch OHLCV data
    log.info(f"Hämtar {cfg.LIMIT} candles för {cfg.SYMBOL} på {cfg.TIMEFRAME}")
    ohlcv = exchange.fetch_ohlcv(cfg.SYMBOL, cfg.TIMEFRAME, limit=cfg.LIMIT)

    # Build DataFrame
    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    # Calculate indicators
    data = calculate_indicators(
        df,
        ema_length=cfg.EMA_LENGTH,
        volume_multiplier=cfg.VOLUME_MULTIPLIER,
        trading_start_hour=cfg.TRADING_START_HOUR,
        trading_end_hour=cfg.TRADING_END_HOUR
    )

    # Detect bullish FVG breakout
    low_zone, high_zone = detect_fvg(data, cfg.LOOKBACK, bullish=True)
    last = data.iloc[-1]

    # Entry conditions
    if (
        high_zone
        and last["close"] > high_zone
        and last["close"] > last["ema"]
        and last["high_volume"]
        and last["within_trading_hours"]
    ):
        entry_price = last["close"]
        sl_price = entry_price * (1 - cfg.STOP_LOSS_PERCENT / 100)
        tp_price = entry_price * (1 + cfg.TAKE_PROFIT_PERCENT / 100)

        # Fetch account equity in quote currency
        quote = cfg.SYMBOL.split(":")[-1]
        balance_info = fetch_balance(exchange)
        equity = balance_info.get("total", {}).get(quote, 0)

        # Calculate position size based on risk per trade
        size = calculate_position_size(
            equity=equity,
            risk_per_trade=cfg.RISK_PER_TRADE,
            entry_price=entry_price,
            stop_loss_price=sl_price
        )

        log.info(
            f"Köp-signal: size={size:.6f}, entry={entry_price:.2f}, "
            f"SL={sl_price:.2f}, TP={tp_price:.2f}"
        )

        # Place market buy order
        buy_order = place_order("buy", cfg.SYMBOL, size)
        log.info(f"Buy order sent: {buy_order}")

                # Place OCO orders: TP limit and SL stop-limit
        try:
            # TP: Limit sell at tp_price
            tp_order = exchange.create_limit_sell_order(cfg.SYMBOL, size, tp_price)
            # SL: Stop-limit sell at sl_price
            sl_order = exchange.create_order(
                cfg.SYMBOL,
                'stop_limit',
                'sell',
                size,
                sl_price,
                {'stopPrice': sl_price}
            )
            tp_id = tp_order.get('id')
            sl_id = sl_order.get('id')
            log.info(
                f"OCO orders placed: TP_order={tp_id}, SL_order={sl_id}"
            )

            # Monitor OCO: cancel the opposite order when one is executed
            while True:
                await asyncio.sleep(5)  # poll every 5 seconds
                try:
                    # Fetch order statuses
                    tp_status = exchange.fetch_order(tp_id, cfg.SYMBOL).get('status')
                    sl_status = exchange.fetch_order(sl_id, cfg.SYMBOL).get('status')
                except Exception as err:
                    log.error(f"Error fetching OCO order status: {err}")
                    continue

                if tp_status == 'closed':
                    # TP executed, cancel SL
                    try:
                        exchange.cancel_order(sl_id, cfg.SYMBOL)
                        log.info(f"SL order {sl_id} canceled after TP execution")
                    except Exception as e:
                        log.error(f"Failed to cancel SL order {sl_id}: {e}")
                    break

                if sl_status == 'closed':
                    # SL executed, cancel TP
                    try:
                        exchange.cancel_order(tp_id, cfg.SYMBOL)
                        log.info(f"TP order {tp_id} canceled after SL execution")
                    except Exception as e:
                        log.error(f"Failed to cancel TP order {tp_id}: {e}")
                    break

        except Exception as e:
            log.error(f"Misslyckades placera eller övervaka OCO orders: {e}")

    # Sleep until next cycle
    await asyncio.sleep(60)
    await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
