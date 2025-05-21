import argparse
import pandas as pd
from config_loader import load_config
from modules.indicators import calculate_indicators, detect_fvg
from modules.orders import calculate_position_size


def run_backtest(data_file: str, config_file: str, initial_equity: float = 10000.0, hold_bars: int = 1):
    """
    Backtest with position sizing, stop-loss and take-profit based on risk parameters.

    :param data_file: CSV file with OHLCV data
    :param config_file: Path to config.json for strategy parameters
    :param initial_equity: Starting account equity
    :param hold_bars: Number of candles to hold a position if TP/SL not hit
    """
    df = pd.read_csv(data_file, parse_dates=['timestamp'])
    cfg = load_config(config_file)

    df = calculate_indicators(
        df,
        ema_length=cfg.EMA_LENGTH,
        volume_multiplier=cfg.VOLUME_MULTIPLIER,
        trading_start_hour=cfg.TRADING_START_HOUR,
        trading_end_hour=cfg.TRADING_END_HOUR,
    )

    equity = initial_equity
    positions = []
    open_pos = None

    for i in range(cfg.LOOKBACK, len(df) - 1):
        price = df.at[i, 'close']

        # Entry on bullish FVG breakout
        if open_pos is None:
            low, high = detect_fvg(df.iloc[:i+1], cfg.LOOKBACK, bullish=True)
            if high and price > high:
                entry_price = df.at[i+1, 'open']
                sl_price = entry_price * (1 - cfg.STOP_LOSS_PERCENT / 100)
                tp_price = entry_price * (1 + cfg.TAKE_PROFIT_PERCENT / 100)
                size = calculate_position_size(
                    equity, cfg.RISK_PER_TRADE, entry_price, sl_price
                )
                open_pos = {
                    'entry_idx': i+1,
                    'entry_price': entry_price,
                    'sl_price': sl_price,
                    'tp_price': tp_price,
                    'size': size
                }
                continue

        # If position is open, check SL/TP or hold duration
        if open_pos:
            # Check stop-loss
            curr_low = df.at[i, 'low']
            if curr_low <= open_pos['sl_price']:
                exit_price = open_pos['sl_price']
                reason = 'SL'
            # Check take-profit
            elif df.at[i, 'high'] >= open_pos['tp_price']:
                exit_price = open_pos['tp_price']
                reason = 'TP'
            # Check hold duration
            elif i >= open_pos['entry_idx'] + hold_bars:
                exit_price = df.at[i+1, 'open']
                reason = 'TIME'
            else:
                continue

            pnl = open_pos['size'] * (exit_price - open_pos['entry_price'])
            equity += pnl
            positions.append({
                'entry_idx': open_pos['entry_idx'],
                'exit_idx': i,
                'entry_price': open_pos['entry_price'],
                'exit_price': exit_price,
                'size': open_pos['size'],
                'pnl': pnl,
                'equity': equity,
                'reason': reason
            })
            open_pos = None

    results = pd.DataFrame(positions)
    results['cumulative_pnl'] = results['pnl'].cumsum()

    output_csv = 'backtest_results.csv'
    results.to_csv(output_csv, index=False)

    total_pnl = results['pnl'].sum()
    print(f"Backtest complete: {len(results)} trades, Total PnL: {total_pnl:.2f}, Final Equity: {equity:.2f}")
    print(f"Results saved to {output_csv}")
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Backtest strategy with SL/TP and risk sizing'
    )
    parser.add_argument('-d', '--data-file', required=True, help='CSV with OHLCV data')
    parser.add_argument('-c', '--config', default='config.json', help='Path to config.json')
    parser.add_argument('-ie', '--initial-equity', type=float, default=10000.0,
                        help='Starting account equity')
    parser.add_argument('-hb', '--hold-bars', type=int, default=1,
                        help='Candles to hold position if no SL/TP')
    args = parser.parse_args()

    run_backtest(args.data_file, args.config, args.initial_equity, args.hold_bars)
