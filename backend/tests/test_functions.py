import os
import json
import time
from datetime import datetime
from colorama import init, Fore, Style
import logging
import sys
import pytest

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.orders import (
    fetch_balance,
    place_order,
    calculate_position_size
)
from src.modules.indicators import calculate_indicators, calculate_ema, calculate_rsi
import pandas as pd
from tests.test_helpers import run_async_test

# Initialize colorama
init()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_trade_execution(order, side, size):
    """Validate trade execution"""
    assert order is not None, f"{side.capitalize()} order should not be None"
    assert order['status'] in ['open', 'closed'], f"{side.capitalize()} order should be open or closed"
    assert order['side'] == side, f"Order side should be {side}"
    
    # Use a small tolerance for float comparison
    tolerance = 1e-8
    assert abs(float(order['amount']) - size) < tolerance, f"Order amount {order['amount']} should be close to {size}"

@pytest.mark.integration
def test_bot_control(bot):
    """Test bot control functions"""
    logger.info(f"\n{Fore.CYAN}=== Testing Bot Control ==={Style.RESET_ALL}")
    
    # Test start
    bot.start()
    assert bot.is_running, "Bot should be running after start"
    
    # Test stop
    bot.stop()
    assert not bot.is_running, "Bot should not be running after stop"

@pytest.mark.integration
def test_balance_fetch(bot):
    """Test balance fetching"""
    logger.info(f"\n{Fore.CYAN}=== Testing Balance Fetch ==={Style.RESET_ALL}")
    
    try:
        # Start bot first
        bot.start()
        assert bot.is_running, "Bot should be running"
        assert bot.exchange is not None, "Exchange should be initialized"
        
        # Verify API credentials
        if not bot.cfg.API_KEY or not bot.cfg.API_SECRET:
            pytest.skip("API credentials not found in .env file")
        
        balance = fetch_balance(bot.exchange)
        logger.info(f"Balance fetched: {balance}")
        
        assert balance is not None, "Balance should not be None"
        assert 'total' in balance, "Balance should have 'total' key"
        assert 'TESTUSD' in balance['total'], "Balance should have TESTUSD"
        assert 'TESTBTC' in balance['total'], "Balance should have TESTBTC"
        
    except Exception as e:
        logger.error(f"{Fore.RED}Balance fetch test failed: {str(e)}{Style.RESET_ALL}")
        pytest.fail(f"Balance fetch test failed: {str(e)}")
    finally:
        bot.stop()

@pytest.mark.integration
def test_trade_execution(bot):
    """Test trade execution"""
    logger.info(f"\n{Fore.CYAN}=== Testing Trade Execution ==={Style.RESET_ALL}")
    
    try:
        # Start bot first
        bot.start()
        assert bot.is_running, "Bot should be running"
        assert bot.exchange is not None, "Exchange should be initialized"
        
        # Verify API credentials
        if not bot.cfg.API_KEY or not bot.cfg.API_SECRET:
            pytest.skip("API credentials not found in .env file")
        
        # Get current price and balance
        ticker = bot.exchange.fetch_ticker('TESTBTC/TESTUSD')
        current_price = ticker['last']
        logger.info(f"Current price: {current_price}")
        
        balance = fetch_balance(bot.exchange)
        equity = balance['total']['TESTUSD']
        logger.info(f"Account equity: {equity} TESTUSD")
        
        # Calculate stop loss price
        sl_price = current_price * (1 - bot.cfg.STOP_LOSS_PERCENT / 100)
        logger.info(f"Stop loss price: {sl_price}")
        
        # Calculate position size
        size = calculate_position_size(
            equity,
            bot.cfg.RISK_PER_TRADE,
            current_price,
            sl_price
        )
        logger.info(f"Calculated position size: {size}")
        
        # Ensure minimum order size
        MIN_ORDER_SIZE = 0.0002  # Minimum order size for BTC/USD
        if size < MIN_ORDER_SIZE:
            logger.warning(f"Position size {size} is below minimum {MIN_ORDER_SIZE}, adjusting...")
            size = MIN_ORDER_SIZE
        
        # Test buy
        logger.info("Testing buy order...")
        buy_order = bot.exchange.create_market_order('TESTBTC/TESTUSD', 'buy', size)
        logger.info(f"Buy order placed: {buy_order}")
        
        # Validate buy order
        validate_trade_execution(buy_order, 'buy', size)
        
        # Wait a bit
        time.sleep(2)
        
        # Test sell
        logger.info("Testing sell order...")
        sell_order = bot.exchange.create_market_order('TESTBTC/TESTUSD', 'sell', size)
        logger.info(f"Sell order placed: {sell_order}")
        
        # Validate sell order
        validate_trade_execution(sell_order, 'sell', size)
        
    except Exception as e:
        logger.error(f"{Fore.RED}Trade execution test failed: {str(e)}{Style.RESET_ALL}")
        pytest.fail(f"Trade execution test failed: {str(e)}")
    finally:
        bot.stop()

@pytest.mark.integration
def test_ohlcv_fetch(bot):
    """Test OHLCV data fetching"""
    logger.info(f"\n{Fore.CYAN}=== Testing OHLCV Fetch ==={Style.RESET_ALL}")
    
    try:
        # Start bot first
        bot.start()
        assert bot.is_running, "Bot should be running"
        assert bot.exchange is not None, "Exchange should be initialized"
        
        ohlcv = bot.exchange.fetch_ohlcv('BTC/USD', bot.cfg.TIMEFRAME, limit=bot.cfg.LIMIT)
        logger.info(f"OHLCV data fetched: {len(ohlcv)} candles")
        
        assert len(ohlcv) > 0, "Should fetch some OHLCV data"
        assert len(ohlcv[0]) == 6, "Each candle should have 6 values"
        
    except Exception as e:
        logger.error(f"{Fore.RED}OHLCV fetch test failed: {str(e)}{Style.RESET_ALL}")
        pytest.fail(f"OHLCV fetch test failed: {str(e)}")
    finally:
        bot.stop()

@pytest.mark.integration
def test_indicators(bot):
    """Test technical indicators"""
    logger.info(f"\n{Fore.CYAN}=== Testing Indicators ==={Style.RESET_ALL}")
    
    try:
        # Start bot first
        bot.start()
        assert bot.is_running, "Bot should be running"
        assert bot.exchange is not None, "Exchange should be initialized"
        
        # Fetch OHLCV data
        ohlcv = bot.exchange.fetch_ohlcv('BTC/USD', bot.cfg.TIMEFRAME, limit=bot.cfg.LIMIT)
        closes = [candle[4] for candle in ohlcv]
        
        # Test EMA
        ema_fast = calculate_ema(closes, bot.cfg.EMA_FAST)
        ema_slow = calculate_ema(closes, bot.cfg.EMA_SLOW)
        logger.info(f"EMA Fast: {ema_fast[-1]}")
        logger.info(f"EMA Slow: {ema_slow[-1]}")
        
        assert len(ema_fast) == len(closes), "EMA Fast should have same length as closes"
        assert len(ema_slow) == len(closes), "EMA Slow should have same length as closes"
        
        # Test RSI
        rsi = calculate_rsi(closes, bot.cfg.RSI_PERIOD)
        logger.info(f"RSI: {rsi[-1]}")
        
        assert len(rsi) == len(closes), "RSI should have same length as closes"
        assert 0 <= rsi[-1] <= 100, "RSI should be between 0 and 100"
        
    except Exception as e:
        logger.error(f"{Fore.RED}Indicators test failed: {str(e)}{Style.RESET_ALL}")
        pytest.fail(f"Indicators test failed: {str(e)}")
    finally:
        bot.stop()

@pytest.mark.integration
def test_async_functions(bot):
    """Test async functions"""
    logger.info(f"\n{Fore.CYAN}=== Testing Async Functions ==={Style.RESET_ALL}")
    
    try:
        # Test async functions
        bot.start()
        time.sleep(5)  # Let it run for a bit
        bot.stop()
        
    except Exception as e:
        logger.error(f"{Fore.RED}Async functions test failed: {str(e)}{Style.RESET_ALL}")
        pytest.fail(f"Async functions test failed: {str(e)}") 