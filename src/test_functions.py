import os
import json
import time
from datetime import datetime
from colorama import init, Fore, Style
import logging
from config_loader import load_config
from modules.orders import init_exchange, fetch_balance, place_order
from modules.indicators import calculate_indicators
from tradingbot import TradingBot
import pandas as pd

# Initialize colorama
init()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def calculate_position_size(balance, price, risk_percentage=0.02):
    """Calculate position size based on available balance and risk percentage"""
    risk_amount = balance * risk_percentage
    position_size = risk_amount / price
    return position_size

class FunctionTester:
    def __init__(self):
        self.cfg = load_config()
        self.exchange = None
        self.bot = None
        self.test_results = {
            "bot_control": {},
            "balance": {},
            "trade_execution": {},
            "ohlcv": {},
            "indicators": {}
        }

    def setup(self):
        """Initialize exchange and bot"""
        logger.info(f"{Fore.CYAN}=== Setting up test environment ==={Style.RESET_ALL}")
        try:
            self.exchange = init_exchange(self.cfg.API_KEY, self.cfg.API_SECRET, self.cfg.EXCHANGE)
            logger.info(f"{Fore.GREEN}Exchange initialized successfully{Style.RESET_ALL}")
            
            self.bot = TradingBot(self.cfg)
            logger.info(f"{Fore.GREEN}Bot initialized successfully{Style.RESET_ALL}")
            
            return True
        except Exception as e:
            logger.error(f"{Fore.RED}Setup failed: {str(e)}{Style.RESET_ALL}")
            return False

    def test_bot_control(self):
        """Test bot start/stop functionality"""
        logger.info(f"\n{Fore.CYAN}=== Testing Bot Control ==={Style.RESET_ALL}")
        
        try:
            # Test start
            logger.info("Testing bot start...")
            start_success = self.bot.start()
            logger.info(f"Bot start {'successful' if start_success else 'failed'}")
            
            # Wait a bit
            time.sleep(2)
            
            # Test stop
            logger.info("Testing bot stop...")
            stop_success = self.bot.stop()
            logger.info(f"Bot stop {'successful' if stop_success else 'failed'}")
            
            self.test_results['bot_control'] = {
                'start_success': start_success,
                'stop_success': stop_success,
                'is_running': self.bot.is_running
            }
            
        except Exception as e:
            logger.error(f"{Fore.RED}Bot control test failed: {str(e)}{Style.RESET_ALL}")
            self.test_results['bot_control'] = {'error': str(e)}

    def test_balance_fetch(self):
        """Test balance fetching"""
        logger.info(f"\n{Fore.CYAN}=== Testing Balance Fetch ==={Style.RESET_ALL}")
        
        try:
            balance = fetch_balance(self.exchange)
            logger.info(f"Balance fetched: {json.dumps(balance, indent=2)}")
            
            self.test_results['balance'] = {
                'success': True,
                'balance': balance
            }
            
        except Exception as e:
            logger.error(f"{Fore.RED}Balance fetch test failed: {str(e)}{Style.RESET_ALL}")
            self.test_results['balance'] = {'error': str(e)}

    def test_trade_execution(self):
        """Test trade execution"""
        logger.info(f"\n{Fore.CYAN}=== Testing Trade Execution ==={Style.RESET_ALL}")
        
        try:
            # Get current price and balance
            ticker = self.exchange.fetch_ticker(self.cfg.SYMBOL)
            current_price = ticker['last']
            balance = fetch_balance(self.exchange)
            quote = self.cfg.SYMBOL.split(":")[-1]
            equity = balance.get("total", {}).get(quote, 0)
            
            # Calculate position size
            sl_price = current_price * (1 - self.cfg.STOP_LOSS_PERCENT / 100)
            size = calculate_position_size(
                equity,
                current_price,
                self.cfg.RISK_PER_TRADE
            )
            
            # Test buy
            logger.info("Testing buy order...")
            buy_order = place_order('buy', self.cfg.SYMBOL, size)
            logger.info(f"Buy order placed: {json.dumps(buy_order, indent=2)}")
            
            # Wait a bit
            time.sleep(2)
            
            # Test sell
            logger.info("Testing sell order...")
            sell_order = place_order('sell', self.cfg.SYMBOL, size)
            logger.info(f"Sell order placed: {json.dumps(sell_order, indent=2)}")
            
            self.test_results['trade_execution'] = {
                'buy_success': bool(buy_order),
                'sell_success': bool(sell_order),
                'buy_order': buy_order,
                'sell_order': sell_order
            }
            
        except Exception as e:
            logger.error(f"{Fore.RED}Trade execution test failed: {str(e)}{Style.RESET_ALL}")
            self.test_results['trade_execution'] = {'error': str(e)}

    def test_ohlcv_fetch(self):
        """Test OHLCV data fetching"""
        logger.info(f"\n{Fore.CYAN}=== Testing OHLCV Fetch ==={Style.RESET_ALL}")
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.cfg.SYMBOL, self.cfg.TIMEFRAME, limit=self.cfg.LIMIT)
            logger.info(f"Fetched {len(ohlcv)} candles")
            logger.info(f"First candle: {ohlcv[0]}")
            logger.info(f"Last candle: {ohlcv[-1]}")
            
            self.test_results['ohlcv'] = {
                'success': True,
                'candle_count': len(ohlcv),
                'first_candle': ohlcv[0],
                'last_candle': ohlcv[-1]
            }
            
        except Exception as e:
            logger.error(f"{Fore.RED}OHLCV fetch test failed: {str(e)}{Style.RESET_ALL}")
            self.test_results['ohlcv'] = {'error': str(e)}

    def test_indicators(self):
        """Test indicator calculations"""
        logger.info(f"\n{Fore.CYAN}=== Testing Indicators ==={Style.RESET_ALL}")
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.cfg.SYMBOL, self.cfg.TIMEFRAME, limit=self.cfg.LIMIT)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            
            indicators = calculate_indicators(
                df,
                ema_length=self.cfg.EMA_LENGTH,
                volume_multiplier=self.cfg.VOLUME_MULTIPLIER,
                trading_start_hour=self.cfg.TRADING_START_HOUR,
                trading_end_hour=self.cfg.TRADING_END_HOUR
            )
            logger.info(f"Indicators calculated successfully")
            
            self.test_results['indicators'] = {
                'success': True,
                'indicators': indicators.to_dict()
            }
            
        except Exception as e:
            logger.error(f"{Fore.RED}Indicators test failed: {str(e)}{Style.RESET_ALL}")
            self.test_results['indicators'] = {'error': str(e)}

    def run_all_tests(self):
        """Run all tests"""
        logger.info(f"{Fore.CYAN}=== Starting Function Tests ==={Style.RESET_ALL}")
        
        if not self.setup():
            logger.error(f"{Fore.RED}Test setup failed. Aborting tests.{Style.RESET_ALL}")
            return
        
        self.test_bot_control()
        self.test_balance_fetch()
        self.test_trade_execution()
        self.test_ohlcv_fetch()
        self.test_indicators()
        
        # Convert Timestamp objects to strings before saving
        def convert_timestamps(obj):
            if isinstance(obj, pd.Timestamp):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(obj, dict):
                return {k: convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps(item) for item in obj]
            return obj
            
        self.test_results = convert_timestamps(self.test_results)
        
        with open(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"\n{Fore.CYAN}=== Test Results Summary ==={Style.RESET_ALL}")
        for test_name, result in self.test_results.items():
            if 'error' in result:
                logger.error(f"{Fore.RED}{test_name}: Failed - {result['error']}{Style.RESET_ALL}")
            else:
                logger.info(f"{Fore.GREEN}{test_name}: Passed{Style.RESET_ALL}")

def main():
    tester = FunctionTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 