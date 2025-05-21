import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch
import json
import ccxt
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config_loader import BotConfig, load_config
from src.tradingbot import TradingBot
from src.modules.orders import init_exchange

# Load environment variables
load_dotenv()

# Test fixtures
@pytest.fixture
def config():
    """Create a test configuration using load_config"""
    try:
        return load_config("config.json")
    except FileNotFoundError:
        # Fallback to default test config if config.json doesn't exist
        return BotConfig(
            API_KEY=os.getenv('API_KEY'),
            API_SECRET=os.getenv('API_SECRET'),
            EXCHANGE='bitfinex',
            SYMBOL='BTC/USD',
            TIMEFRAME='1h',
            LIMIT=100,
            RISK_PER_TRADE=0.01,
            STOP_LOSS_PERCENT=2.0,
            TAKE_PROFIT_PERCENT=4.0,
            EMA_LENGTH=20,
            EMA_FAST=12,
            EMA_SLOW=26,
            RSI_PERIOD=14,
            VOLUME_MULTIPLIER=1.5,
            TRADING_START_HOUR=0,
            TRADING_END_HOUR=24,
            ATR_MULTIPLIER=2.0,
            MAX_DAILY_LOSS=2.0,
            MAX_TRADES_PER_DAY=5,
            LOOKBACK=5,
            EMAIL_ENABLED=False,
            EMAIL_SMTP_SERVER=None,
            EMAIL_SMTP_PORT=None,
            EMAIL_SENDER=None,
            EMAIL_RECEIVER=None,
            EMAIL_PASSWORD=None,
            METRICS_PORT=5000,
            HEALTH_PORT=5001
        )

@pytest.fixture
def exchange(config):
    """Create an exchange instance for testing"""
    if not config.API_KEY or not config.API_SECRET:
        pytest.skip("API credentials not found in .env file")
        
    exchange = ccxt.bitfinex({
        'apiKey': config.API_KEY,
        'secret': config.API_SECRET,
        'enableRateLimit': True,
        'options': {
            'paper': True,  # Enable paper trading
            'defaultType': 'spot'
        }
    })
    exchange.load_markets()
    return exchange

@pytest.fixture
def bot(config):
    """Create a trading bot instance for testing"""
    if not config.API_KEY or not config.API_SECRET:
        pytest.skip("API credentials not found in .env file")
    return TradingBot(config)

@pytest.fixture
def sample_ohlcv_data():
    """Skapar exempel OHLCV-data för testerna"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    data = {
        'timestamp': [int(d.timestamp() * 1000) for d in dates],
        'open': np.random.normal(50000, 1000, 100),
        'high': np.random.normal(51000, 1000, 100),
        'low': np.random.normal(49000, 1000, 100),
        'close': np.random.normal(50000, 1000, 100),
        'volume': np.random.normal(100, 10, 100)
    }
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    return df

# Hjälpfunktioner
def create_test_order(order_type='buy', amount=0.1, price=50000.0):
    """Skapar en testorder"""
    return {
        'id': 'test_order_1',
        'type': order_type,
        'amount': amount,
        'price': price,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'status': 'closed'
    }

def validate_trade_execution(order, expected_type, expected_amount, tolerance=0.0001):
    """Validerar att en trade utfördes korrekt"""
    assert order['type'] == expected_type
    assert abs(order['amount'] - expected_amount) < tolerance
    assert order['status'] == 'closed'

async def run_async_test(coro):
    """Kör en asynkron testfunktion"""
    try:
        return await asyncio.wait_for(coro, timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail("Test timeout")

def save_test_results(results, test_name):
    """Sparar testresultat till JSON-fil"""
    os.makedirs('test_results', exist_ok=True)
    filename = f'test_results_{test_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(os.path.join('test_results', filename), 'w') as f:
        json.dump(results, f, indent=2)

# Event hooks
def pytest_configure(config):
    """Konfigurerar pytest"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(items):
    """Modifierar testcollection"""
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)
