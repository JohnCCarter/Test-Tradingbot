import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import atexit
import json
import logging
import signal
import socket
import threading
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import pandas as pd
from colorama import Back, Fore, Style, init
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from .config_loader import load_config
from .modules.indicators import calculate_indicators
from .modules.orders import fetch_balance, init_exchange, place_order
from .tradingbot import TradingBot

# Initialize colorama for Windows
init()


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Back.WHITE,
    }

    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
            )

        # Add color to the message based on level
        if record.levelname == "ERROR":
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        elif record.levelname == "WARNING":
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"

        return super().format(record)


def setup_logging():
    """Setup logging with colors, formatting and rotation"""
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for important logs with rotation
    today = datetime.now().strftime("%Y%m%d")
    general_log_file = os.path.join(logs_dir, f"dashboard_{today}.log")
    file_handler = RotatingFileHandler(
        general_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # Keep 5 backup files
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Bot error logger with rotation
    bot_logger = logging.getLogger("bot_errors")
    bot_logger.setLevel(logging.ERROR)
    bot_log_file = os.path.join(logs_dir, f"bot_errors_{today}.log")
    bot_file_handler = RotatingFileHandler(
        bot_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,  # Keep 3 backup files
        encoding="utf-8",
    )
    bot_file_handler.setLevel(logging.ERROR)
    bot_file_handler.setFormatter(file_formatter)
    bot_logger.addHandler(bot_file_handler)

    # Add filters to remove unnecessary information
    for handler in [file_handler, bot_file_handler]:
        handler.addFilter(
            lambda record: not record.getMessage().startswith("Request URL:")
        )
        handler.addFilter(
            lambda record: not record.getMessage().startswith("Request Method:")
        )
        handler.addFilter(
            lambda record: not record.getMessage().startswith("Request Headers:")
        )
        handler.addFilter(
            lambda record: not record.getMessage().startswith("Request JSON:")
        )
        handler.addFilter(
            lambda record: not record.getMessage().startswith("Request Form Data:")
        )
        handler.addFilter(
            lambda record: not record.getMessage().startswith("Request Args:")
        )

    return root_logger, bot_logger


# Setup logging
logger, bot_logger = setup_logging()

logger.debug("Starting dashboard.py")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
logger.debug("Loading configuration...")
cfg = load_config()
logger.debug("Configuration loaded: %s", cfg)

# Initialize trading bot
bot = TradingBot(cfg)


def print_banner():
    """Print a nice banner when starting the dashboard"""
    banner = f"""
==================================================
                Trading Bot Dashboard                    
- Status: Running                                     
- Port: {cfg.METRICS_PORT}                                            
- URL: http://127.0.0.1:{cfg.METRICS_PORT}                        
==================================================
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
    if logger.getEffectiveLevel() == logging.DEBUG:
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
║{Fore.GREEN}● Bot Status: {'Running' if getattr(bot, 'is_running', False) else 'Stopped'}{Fore.WHITE}                    ║
║{Fore.YELLOW}● Last Update: {trading_state.get('last_update')}{Fore.WHITE}                ║
║{Fore.BLUE}● Active Trades: {len(getattr(bot, 'trade_history', []))}{Fore.WHITE}                                ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(status)


def cleanup():
    """Cleanup function to be called on exit"""
    try:
        # Stop the bot if it's running
        if bot.is_running:
            bot.stop()
        # Kill any process using our port
        if os.name == "nt":  # Windows
            os.system(
                f"netstat -ano | findstr :{cfg.METRICS_PORT} > nul && taskkill /F /PID %ERRORLEVEL%"
            )
        else:  # Unix/Linux
            os.system(f"lsof -ti:{cfg.METRICS_PORT} | xargs kill -9")
    except Exception as e:
        logger.error("Error during cleanup: %s", e)
    finally:
        # Ensure all handlers are closed
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


# Register cleanup function
atexit.register(cleanup)


def check_port(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
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
    "is_running": False,
    "current_position": None,
    "balance": None,
    "last_update": None,
    "metrics": {
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "total_pnl": 0.0,
        "win_rate": 0.0,
    },
    "ohlcv_data": None,
    "trade_history": [],
    "pnl_history": [],
    "price_alerts": [],
    "price_history": [],
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
            trading_state["is_running"] = bot.is_running
            trading_state["current_position"] = bot.current_position
            trading_state["balance"] = balance
            trading_state["last_update"] = bot.last_update

            # Calculate metrics
            logger.info("Calculating trading metrics...")
            total_trades = len(bot.trade_history)
            winning_trades = len([t for t in bot.trade_history if t["pnl"] > 0])
            losing_trades = len([t for t in bot.trade_history if t["pnl"] <= 0])
            total_pnl = sum(t["pnl"] for t in bot.trade_history)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            trading_state["metrics"] = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "total_pnl": total_pnl,
                "win_rate": win_rate,
            }

            logger.info(
                f"Metrics updated: {json.dumps(trading_state['metrics'], indent=2)}"
            )
            logger.info("--- Metrics Update Cycle Complete ---")

        except Exception as e:
            logger.error(f"Error in update_metrics: {e}", exc_info=True)
            time.sleep(5)  # Wait before retrying
            continue

        time.sleep(5)  # Update every 5 seconds


@app.route("/")
def index():
    """Render main dashboard"""
    logger.info("=== Dashboard Page Request ===")
    try:
        log_request_info()
        logger.info("Rendering dashboard template")
        return render_template("dashboard.html")
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}", exc_info=True)
        return str(e), 500


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Get current metrics"""
    logger.info("=== Metrics Request ===")
    try:
        log_request_info()
        logger.info(f"Current trading state: {json.dumps(trading_state, indent=2)}")
        return jsonify(trading_state)
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    logger.info("=== Health Check Request ===")
    try:
        log_request_info()
        health_status = {
            "status": "healthy",
            "last_update": trading_state["last_update"],
            "bot_running": bot.is_running,
            "exchange_connected": bool(trading_state["balance"]),
            "current_position": bool(trading_state["current_position"]),
        }
        logger.info(f"Health status: {json.dumps(health_status, indent=2)}")
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/trade", methods=["POST"])
def execute_trade():
    try:
        data = request.get_json()
        trade_type = data.get("type")
        amount = data.get("amount")

        if not trade_type or not amount:
            return jsonify({"error": "Missing trade type or amount"}), 400

        if trade_type not in ["buy", "sell"]:
            return jsonify({"error": "Invalid trade type"}), 400

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        # Get the exchange instance
        exchange = init_exchange(cfg.API_KEY, cfg.API_SECRET, cfg.EXCHANGE)

        # Execute the trade
        if trade_type == "buy":
            order = exchange.create_market_buy_order(cfg.SYMBOL, amount)
        else:
            order = exchange.create_market_sell_order(cfg.SYMBOL, amount)

        # Create trade record
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": trade_type,
            "entry_price": order.get("price", 0),
            "size": amount,
            "pnl": 0,  # Will be calculated when position is closed
        }

        # Update trading state
        trading_state["is_running"] = True
        trading_state["current_position"] = order
        trading_state["balance"] = fetch_balance(exchange)
        trading_state["last_update"] = datetime.now().isoformat()

        # Add to trade history
        trading_state["trade_history"].append(trade)

        # Update metrics
        trading_state["metrics"]["total_trades"] += 1
        if trade.get("pnl", 0) > 0:
            trading_state["metrics"]["winning_trades"] += 1
        else:
            trading_state["metrics"]["losing_trades"] += 1
        trading_state["metrics"]["total_pnl"] += trade.get("pnl", 0)
        trading_state["metrics"]["win_rate"] = (
            trading_state["metrics"]["winning_trades"]
            / trading_state["metrics"]["total_trades"]
            * 100
            if trading_state["metrics"]["total_trades"] > 0
            else 0
        )

        return jsonify(
            {
                "message": f"Successfully executed {trade_type} order for {amount} BTC",
                "order": order,
                "trade": trade,
            }
        )

    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/bot/control", methods=["POST"])
def control_bot():
    """Start or stop the trading bot"""
    logger.info("=== Bot Control Request ===")
    try:
        log_request_info()
        data = request.get_json()
        action = data.get("action")

        logger.info(f"Bot control action requested: {action}")

        if action not in ["start", "stop"]:
            error_msg = f"Invalid bot action: {action}"
            logger.error(error_msg)
            return jsonify({"success": False, "error": error_msg})

        if action == "start":
            logger.info("Attempting to start bot...")
            success = bot.start()
            logger.info(f"Bot start {'successful' if success else 'failed'}")
        else:
            logger.info("Attempting to stop bot...")
            success = bot.stop()
            logger.info(f"Bot stop {'successful' if success else 'failed'}")

        logger.info(f"Bot running status: {bot.is_running}")
        return jsonify({"success": success, "is_running": bot.is_running})
    except Exception as e:
        error_msg = f"Error controlling bot: {str(e)}"
        log_bot_error(error_msg, e)
        return jsonify({"success": False, "error": error_msg})


@app.route("/api/ohlcv")
def get_ohlcv():
    """Get OHLCV data for charts"""
    logger.info("=== OHLCV Data Request ===")
    try:
        log_request_info()
        logger.info("Initializing exchange for OHLCV data...")
        exchange = init_exchange(cfg.API_KEY, cfg.API_SECRET, cfg.EXCHANGE)

        logger.info(
            f"Fetching OHLCV data for {cfg.SYMBOL} on {cfg.TIMEFRAME} timeframe..."
        )
        ohlcv = exchange.fetch_ohlcv(cfg.SYMBOL, cfg.TIMEFRAME, limit=cfg.LIMIT)
        logger.info(f"Fetched {len(ohlcv)} candles")

        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        logger.info(f"OHLCV data processed. First candle: {df.iloc[0].to_dict()}")
        logger.info(f"Last candle: {df.iloc[-1].to_dict()}")

        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        error_msg = f"Error fetching OHLCV data: {str(e)}"
        log_bot_error(error_msg, e)
        return jsonify([])


@app.route("/api/trades")
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
        with open("config.json", "w") as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False


@app.route("/api/settings", methods=["GET"])
def get_settings():
    # Ladda endast från filen för att skicka till frontend
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return jsonify(config)
    except FileNotFoundError:
        logger.warning("config.json not found, returning empty settings.")
        return jsonify({})
    except Exception as e:
        logger.error(f"Error loading config for GET: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/settings", methods=["POST"])
def update_settings():
    try:
        new_settings = request.json

        # Ladda befintlig konfiguration från filen
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        except FileNotFoundError:
            config_dict = {}

        # Uppdatera endast tillåtna inställningar
        allowed_settings = {
            "EMA_LENGTH",
            "ATR_MULTIPLIER",
            "VOLUME_MULTIPLIER",
            "TRADING_START_HOUR",
            "TRADING_END_HOUR",
            "MAX_DAILY_LOSS",
            "MAX_TRADES_PER_DAY",
            "LOOKBACK",
            "STOP_LOSS_PERCENT",
            "TAKE_PROFIT_PERCENT",
            "RISK_PER_TRADE",
        }

        if new_settings is None:
            return jsonify({"status": "error", "message": "No settings provided"}), 400

        for key, value in new_settings.items():
            if key in allowed_settings:
                config_dict[key] = value

        # Spara det uppdaterade dictionaryt till filen
        if save_config(config_dict):
            return jsonify({"status": "success", "message": "Settings updated"})
        else:
            return (
                jsonify({"status": "error", "message": "Failed to save settings"}),
                500,
            )

    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/toggle", methods=["POST"])
def toggle_bot():
    try:
        if not request.json:
            return jsonify({"status": "error", "message": "No action provided"}), 400

        action = request.json.get("action")
        if not action or action not in ["start", "stop"]:
            return jsonify({"status": "error", "message": "Invalid action"}), 400

        trading_state["is_running"] = action == "start"
        return jsonify(
            {
                "status": "success",
                "message": f"Bot {'started' if action == 'start' else 'stopped'}",
                "is_running": trading_state["is_running"],
            }
        )

    except Exception as e:
        logger.error(f"Error toggling bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/price", methods=["GET"])
def get_current_price():
    """Get current price"""
    logger.info("=== Price Request ===")
    try:
        log_request_info()
        exchange = init_exchange(cfg.API_KEY, cfg.API_SECRET, cfg.EXCHANGE)
        ticker = exchange.fetch_ticker(cfg.SYMBOL)

        current_price = ticker["last"]
        timestamp = ticker["timestamp"]

        # Add to price history
        trading_state["price_history"].append(
            {"price": current_price, "timestamp": timestamp}
        )

        # Keep only last 1000 price points
        if len(trading_state["price_history"]) > 1000:
            trading_state["price_history"] = trading_state["price_history"][-1000:]

        logger.info(f"Current price: {current_price}")
        return jsonify(
            {
                "price": current_price,
                "bid": ticker["bid"],
                "ask": ticker["ask"],
                "volume": ticker["baseVolume"],
                "timestamp": timestamp,
            }
        )
    except Exception as e:
        logger.error(f"Error fetching price: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/price/alerts", methods=["POST"])
def add_price_alert():
    try:
        data = request.get_json()
        alert_type = data.get("type")
        price = data.get("price")

        if not alert_type or not price:
            return jsonify({"error": "Missing alert type or price"}), 400

        if alert_type not in ["above", "below"]:
            return jsonify({"error": "Invalid alert type"}), 400

        trading_state["price_alerts"].append(
            {"type": alert_type, "price": float(price)}
        )

        return jsonify({"message": "Price alert added successfully"})

    except Exception as e:
        logger.error(f"Error adding price alert: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/price/history", methods=["GET"])
def get_price_history():
    """Get price history"""
    logger.info("=== Price History Request ===")
    try:
        log_request_info()
        return jsonify(trading_state["price_history"])
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return jsonify({"error": str(e)}), 500


def start_dashboard():
    """Start the dashboard server"""
    try:
        logger.info("=== Starting Dashboard Server ===")

        # Check if templates directory exists
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        if not os.path.exists(templates_dir):
            logger.error(f"Templates directory not found: {templates_dir}")
            return False

        # Check if dashboard.html exists
        dashboard_template = os.path.join(templates_dir, "dashboard.html")
        if not os.path.exists(dashboard_template):
            logger.error(f"Dashboard template not found: {dashboard_template}")
            return False

        # Print startup banner
        print_banner()

        # Start metrics update thread
        metrics_thread = threading.Thread(target=update_metrics, daemon=True)
        metrics_thread.start()
        logger.info("Metrics update thread started")

        # Register cleanup function to run on exit
        atexit.register(cleanup)

        # Start Flask server
        logger.info(f"Starting Flask server on port {cfg.METRICS_PORT}")
        app.run(host="127.0.0.1", port=cfg.METRICS_PORT, debug=True, use_reloader=False)

        return True
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    start_dashboard()
