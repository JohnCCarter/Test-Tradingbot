from flask import Flask, render_template, jsonify, request
import pandas as pd
from config_loader import load_config
from modules.orders import fetch_balance, init_exchange, place_order
from modules.indicators import calculate_indicators
from tradingbot import TradingBot
import logging
import threading
import time
import os
import socket
import atexit
import signal
import json
from datetime import datetime
from colorama import init, Fore, Back, Style
from flask_cors import CORS

# Initialize colorama for Windows
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }

    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
        
        # Add color to the message based on level
        if record.levelname == 'ERROR':
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        elif record.levelname == 'WARNING':
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        
        return super().format(record)

def setup_logging():
    """Setup logging with colors and formatting"""
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for all logs
    general_log_file = os.path.join(logs_dir, f'dashboard_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(general_log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Bot error logger
    bot_logger = logging.getLogger('bot_errors')
    bot_logger.setLevel(logging.ERROR)
    bot_log_file = os.path.join(logs_dir, f'bot_errors_{datetime.now().strftime("%Y%m%d")}.log')
    bot_file_handler = logging.FileHandler(bot_log_file)
    bot_file_handler.setLevel(logging.ERROR)
    bot_file_handler.setFormatter(file_formatter)
    bot_logger.addHandler(bot_file_handler)

    return root_logger, bot_logger

# Setup logging
logger, bot_logger = setup_logging()

app = Flask(__name__)
CORS(app)
cfg = load_config()

# Initialize trading bot
bot = TradingBot(cfg)

def print_banner():
    """Print a nice banner when starting the dashboard"""
    banner = f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════╗
║{Style.BRIGHT}                Trading Bot Dashboard                    {Style.NORMAL}║
║{Fore.GREEN}● Status: Running{Fore.WHITE}                                         ║
║{Fore.YELLOW}● Port: {cfg.METRICS_PORT}{Fore.WHITE}                                            ║
║{Fore.BLUE}● URL: http://127.0.0.1:{cfg.METRICS_PORT}{Fore.WHITE}                        ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def log_bot_error(error_msg, error=None):
    """Log bot errors to a separate file with stack trace"""
    if error:
        bot_logger.error(f"{error_msg}: {str(error)}", exc_info=True)
        logger.error(f"Bot Error: {error_msg}: {str(error)}", exc_info=True)
    else:
        bot_logger.error(error_msg)
        logger.error(f"Bot Error: {error_msg}")

def log_request_info():
    """Log request information for debugging"""
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    if request.is_json:
        logger.debug(f"Request JSON: {request.get_json()}")
    else:
        logger.debug(f"Request Form Data: {request.form}")
    logger.debug(f"Request Args: {request.args}")

def print_status_update():
    """Print a status update to the console"""
    status = f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════╗
║{Style.BRIGHT}                    Status Update                        {Style.NORMAL}║
║{Fore.GREEN}● Bot Status: {'Running' if bot.is_running else 'Stopped'}{Fore.WHITE}                    ║
║{Fore.YELLOW}● Last Update: {trading_state['last_update']}{Fore.WHITE}                ║
║{Fore.BLUE}● Active Trades: {len(bot.trade_history)}{Fore.WHITE}                                ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(status)

def cleanup():
    """Cleanup function to be called on exit"""
    logger.info("Cleaning up and shutting down...")
    # Stop the bot if it's running
    if bot.is_running:
        bot.stop()
    # Kill any process using our port
    try:
        if os.name == 'nt':  # Windows
            os.system(f'netstat -ano | findstr :{cfg.METRICS_PORT} > nul && taskkill /F /PID %ERRORLEVEL%')
        else:  # Unix/Linux
            os.system(f"lsof -ti:{cfg.METRICS_PORT} | xargs kill -9")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Register cleanup function
atexit.register(cleanup)

def check_port(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except socket.error:
        return False

# Log configuration
logger.info("Configuration loaded:")
logger.info(f"METRICS_PORT: {cfg.METRICS_PORT}")
logger.info(f"HEALTH_PORT: {cfg.HEALTH_PORT}")
logger.info(f"EXCHANGE: {cfg.EXCHANGE}")
logger.info(f"SYMBOL: {cfg.SYMBOL}")

# Check if port is available
if not check_port(cfg.METRICS_PORT):
    logger.error(f"Port {cfg.METRICS_PORT} is already in use!")
    logger.info("Please try a different port in config.json")
    raise RuntimeError(f"Port {cfg.METRICS_PORT} is already in use!")

# Global state
trading_state = {
    'is_running': False,
    'current_position': None,
    'balance': None,
    'last_update': None,
    'metrics': {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_pnl': 0.0,
        'win_rate': 0.0
    },
    'ohlcv_data': None,
    'trade_history': [],
    'pnl_history': []
}

def update_metrics():
    """Background thread to update metrics"""
    logger.info("=== Starting Metrics Update Thread ===")
    while True:
        try:
            logger.info("--- Metrics Update Cycle Start ---")
            # Update balance
            logger.info("Initializing exchange for balance update...")
            exchange = init_exchange(cfg.API_KEY, cfg.API_SECRET, cfg.EXCHANGE)
            logger.info(f"Exchange initialized: {cfg.EXCHANGE}")
            
            logger.info("Fetching current balance...")
            balance = fetch_balance(exchange)
            logger.info(f"Balance fetched: {json.dumps(balance, indent=2)}")
            
            # Update trading state
            logger.info("Updating trading state...")
            trading_state['is_running'] = bot.is_running
            trading_state['current_position'] = bot.current_position
            trading_state['balance'] = balance
            trading_state['last_update'] = bot.last_update
            
            # Calculate metrics
            logger.info("Calculating trading metrics...")
            total_trades = len(bot.trade_history)
            winning_trades = len([t for t in bot.trade_history if t['pnl'] > 0])
            losing_trades = len([t for t in bot.trade_history if t['pnl'] <= 0])
            total_pnl = sum(t['pnl'] for t in bot.trade_history)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            trading_state['metrics'] = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'win_rate': win_rate
            }
            
            logger.info(f"Metrics updated: {json.dumps(trading_state['metrics'], indent=2)}")
            logger.info("--- Metrics Update Cycle Complete ---")
            
        except Exception as e:
            log_bot_error("Error updating metrics", e)
        time.sleep(5)  # Update every 5 seconds

@app.route('/')
def index():
    """Render main dashboard"""
    logger.info("=== Dashboard Page Request ===")
    try:
        log_request_info()
        logger.info("Rendering dashboard template")
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}", exc_info=True)
        return str(e), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current metrics"""
    logger.info("=== Metrics Request ===")
    try:
        log_request_info()
        logger.info(f"Current trading state: {json.dumps(trading_state, indent=2)}")
        return jsonify(trading_state)
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    logger.info("=== Health Check Request ===")
    try:
        log_request_info()
        health_status = {
            'status': 'healthy',
            'last_update': trading_state['last_update'],
            'bot_running': bot.is_running,
            'exchange_connected': bool(trading_state['balance']),
            'current_position': bool(trading_state['current_position'])
        }
        logger.info(f"Health status: {json.dumps(health_status, indent=2)}")
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    try:
        data = request.get_json()
        trade_type = data.get('type')
        amount = data.get('amount')

        if not trade_type or not amount:
            return jsonify({'error': 'Missing trade type or amount'}), 400

        if trade_type not in ['buy', 'sell']:
            return jsonify({'error': 'Invalid trade type'}), 400

        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400

        # Get the exchange instance
        exchange = init_exchange(cfg.API_KEY, cfg.API_SECRET, cfg.EXCHANGE)
        
        # Execute the trade
        if trade_type == 'buy':
            order = exchange.create_market_buy_order(cfg.SYMBOL, amount)
        else:
            order = exchange.create_market_sell_order(cfg.SYMBOL, amount)

        # Update trading state
        trading_state['is_running'] = True
        trading_state['current_position'] = order
        trading_state['balance'] = fetch_balance(exchange)
        trading_state['last_update'] = datetime.now().isoformat()
        
        # Calculate metrics
        trading_state['metrics']['total_trades'] += 1
        if order['pnl'] > 0:
            trading_state['metrics']['winning_trades'] += 1
        else:
            trading_state['metrics']['losing_trades'] += 1
        trading_state['metrics']['total_pnl'] += order['pnl']
        trading_state['metrics']['win_rate'] = (
            trading_state['metrics']['winning_trades'] / 
            trading_state['metrics']['total_trades'] * 100
            if trading_state['metrics']['total_trades'] > 0 else 0
        )

        return jsonify({
            'message': f'Successfully executed {trade_type} order for {amount} BTC',
            'order': order
        })

    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/control', methods=['POST'])
def control_bot():
    """Start or stop the trading bot"""
    logger.info("=== Bot Control Request ===")
    try:
        log_request_info()
        data = request.get_json()
        action = data.get('action')
        
        logger.info(f"Bot control action requested: {action}")
        
        if action not in ['start', 'stop']:
            error_msg = f"Invalid bot action: {action}"
            logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg})
        
        if action == 'start':
            logger.info("Attempting to start bot...")
            success = bot.start()
            logger.info(f"Bot start {'successful' if success else 'failed'}")
        else:
            logger.info("Attempting to stop bot...")
            success = bot.stop()
            logger.info(f"Bot stop {'successful' if success else 'failed'}")
        
        logger.info(f"Bot running status: {bot.is_running}")
        return jsonify({
            'success': success,
            'is_running': bot.is_running
        })
    except Exception as e:
        error_msg = f"Error controlling bot: {str(e)}"
        log_bot_error(error_msg, e)
        return jsonify({
            'success': False,
            'error': error_msg
        })

@app.route('/api/ohlcv')
def get_ohlcv():
    """Get OHLCV data for charts"""
    logger.info("=== OHLCV Data Request ===")
    try:
        log_request_info()
        logger.info("Initializing exchange for OHLCV data...")
        exchange = init_exchange(cfg.API_KEY, cfg.API_SECRET, cfg.EXCHANGE)
        
        logger.info(f"Fetching OHLCV data for {cfg.SYMBOL} on {cfg.TIMEFRAME} timeframe...")
        ohlcv = exchange.fetch_ohlcv(cfg.SYMBOL, cfg.TIMEFRAME, limit=cfg.LIMIT)
        logger.info(f"Fetched {len(ohlcv)} candles")
        
        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        
        logger.info(f"OHLCV data processed. First candle: {df.iloc[0].to_dict()}")
        logger.info(f"Last candle: {df.iloc[-1].to_dict()}")
        
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        error_msg = f"Error fetching OHLCV data: {str(e)}"
        log_bot_error(error_msg, e)
        return jsonify([])

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    logger.info("=== Trade History Request ===")
    try:
        log_request_info()
        logger.info(f"Fetching trade history. Total trades: {len(bot.trade_history)}")
        if bot.trade_history:
            logger.info(f"Latest trade: {json.dumps(bot.trade_history[-1], indent=2)}")
        return jsonify(bot.trade_history)
    except Exception as e:
        error_msg = f"Error fetching trade history: {str(e)}"
        log_bot_error(error_msg, e)
        return jsonify([])

def save_config(config_dict):
    """Save configuration (dictionary) to config.json"""
    try:
        with open('config.json', 'w') as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

@app.route('/api/settings', methods=['GET'])
def get_settings():
    # Ladda endast från filen för att skicka till frontend
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except FileNotFoundError:
        logger.warning("config.json not found, returning empty settings.")
        return jsonify({})
    except Exception as e:
        logger.error(f"Error loading config for GET: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        new_settings = request.json
        
        # Ladda befintlig konfiguration från filen
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        except FileNotFoundError:
            config_dict = {}
            
        # Uppdatera endast tillåtna inställningar
        allowed_settings = {
            'EMA_LENGTH', 'ATR_MULTIPLIER', 'VOLUME_MULTIPLIER',
            'TRADING_START_HOUR', 'TRADING_END_HOUR', 'MAX_DAILY_LOSS',
            'MAX_TRADES_PER_DAY', 'LOOKBACK', 'STOP_LOSS_PERCENT',
            'TAKE_PROFIT_PERCENT', 'RISK_PER_TRADE'
        }
        
        for key, value in new_settings.items():
            if key in allowed_settings:
                config_dict[key] = value
        
        # Spara det uppdaterade dictionaryt till filen
        if save_config(config_dict):
            return jsonify({"status": "success", "message": "Settings updated"})
        else:
            return jsonify({"status": "error", "message": "Failed to save settings"}), 500
            
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/toggle', methods=['POST'])
def toggle_bot():
    try:
        action = request.json.get('action')
        if action not in ['start', 'stop']:
            return jsonify({"status": "error", "message": "Invalid action"}), 400
            
        trading_state['is_running'] = (action == 'start')
        return jsonify({
            "status": "success",
            "message": f"Bot {'started' if action == 'start' else 'stopped'}",
            "is_running": trading_state['is_running']
        })
        
    except Exception as e:
        logger.error(f"Error toggling bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def add_trade():
    try:
        trade = request.json
        trade['timestamp'] = datetime.now().isoformat()
        
        # Lägg till trade i historiken
        trading_state['trade_history'].append(trade)
        
        # Uppdatera PnL-historia
        if 'pnl' in trade:
            trading_state['pnl_history'].append({
                'timestamp': trade['timestamp'],
                'pnl': trade['pnl']
            })
        
        # Uppdatera metrics
        if trade.get('pnl', 0) > 0:
            trading_state['metrics']['winning_trades'] += 1
        else:
            trading_state['metrics']['losing_trades'] += 1
            
        trading_state['metrics']['total_trades'] += 1
        trading_state['metrics']['total_pnl'] += trade.get('pnl', 0)
        trading_state['metrics']['win_rate'] = (
            trading_state['metrics']['winning_trades'] / 
            trading_state['metrics']['total_trades'] * 100
            if trading_state['metrics']['total_trades'] > 0 else 0
        )
        
        return jsonify({"status": "success", "message": "Trade added"})
        
    except Exception as e:
        logger.error(f"Error adding trade: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def start_dashboard():
    """Start the dashboard server"""
    logger.info("=== Starting Dashboard Server ===")
    
    # Check if templates directory exists
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        logger.error(f"Templates directory not found at: {templates_dir}")
        raise RuntimeError(f"Templates directory not found at: {templates_dir}")
    
    # Check if dashboard.html exists
    dashboard_template = os.path.join(templates_dir, 'dashboard.html')
    if not os.path.exists(dashboard_template):
        logger.error(f"dashboard.html not found at: {dashboard_template}")
        raise RuntimeError(f"dashboard.html not found at: {dashboard_template}")
    
    # Kill any existing process on our port
    cleanup()
    
    # Print startup banner
    print_banner()
    
    logger.info("Starting metrics update thread")
    # Start metrics update thread
    metrics_thread = threading.Thread(target=update_metrics, daemon=True)
    metrics_thread.start()
    
    # Start Flask server
    port = cfg.METRICS_PORT
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Server will be available at: http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False)  # Set debug=False to prevent auto-reload

if __name__ == '__main__':
    try:
        start_dashboard()
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}", exc_info=True)
        raise 