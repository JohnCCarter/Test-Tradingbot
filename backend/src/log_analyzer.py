import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
from colorama import Fore, Style, init

# Initialize colorama
init()


class LogAnalyzer:
    def __init__(self, logs_dir="logs"):
        self.logs_dir = logs_dir
        self.dashboard_log = None
        self.bot_errors_log = None
        self.load_latest_logs()

    def load_latest_logs(self):
        """Load the latest log files"""
        today = datetime.now().strftime("%Y%m%d")
        self.dashboard_log = os.path.join(self.logs_dir, f"dashboard_{today}.log")
        self.bot_errors_log = os.path.join(self.logs_dir, f"bot_errors_{today}.log")

    def read_log_file(self, file_path):
        """Read log file and return lines"""
        if not os.path.exists(file_path):
            print(f"{Fore.RED}Log file not found: {file_path}{Style.RESET_ALL}")
            return []
        with open(file_path, "r") as f:
            return f.readlines()

    def analyze_errors(self):
        """Analyze error patterns in logs"""
        print(f"\n{Fore.CYAN}=== Error Analysis ==={Style.RESET_ALL}")

        # Read both log files
        dashboard_lines = self.read_log_file(self.dashboard_log)
        bot_error_lines = self.read_log_file(self.bot_errors_log)

        # Collect errors
        errors = []
        for line in dashboard_lines + bot_error_lines:
            if "ERROR" in line:
                errors.append(line.strip())

        if not errors:
            print(f"{Fore.GREEN}No errors found in logs!{Style.RESET_ALL}")
            return

        # Group errors by type
        error_groups = defaultdict(list)
        for error in errors:
            # Extract error message
            match = re.search(r"ERROR - (.*?)(?:\n|$)", error)
            if match:
                error_msg = match.group(1)
                error_groups[error_msg].append(error)

        # Print error summary
        print(
            f"\n{Fore.YELLOW}Found {len(errors)} errors grouped into {len(error_groups)} types:{Style.RESET_ALL}"
        )
        for error_type, occurrences in error_groups.items():
            print(f"\n{Fore.RED}Error Type: {error_type}{Style.RESET_ALL}")
            print(f"Occurrences: {len(occurrences)}")
            print(f"First occurrence: {occurrences[0]}")
            if len(occurrences) > 1:
                print(f"Last occurrence: {occurrences[-1]}")

    def analyze_bot_status(self):
        """Analyze bot start/stop patterns"""
        print(f"\n{Fore.CYAN}=== Bot Status Analysis ==={Style.RESET_ALL}")

        lines = self.read_log_file(self.dashboard_log)
        bot_events = []

        for line in lines:
            if "Bot control action requested" in line:
                bot_events.append(line.strip())
            elif "Bot running status" in line:
                bot_events.append(line.strip())

        if not bot_events:
            print(f"{Fore.YELLOW}No bot control events found in logs{Style.RESET_ALL}")
            return

        print("\nBot Control Events:")
        for event in bot_events:
            if "start" in event.lower():
                print(f"{Fore.GREEN}{event}{Style.RESET_ALL}")
            elif "stop" in event.lower():
                print(f"{Fore.RED}{event}{Style.RESET_ALL}")
            else:
                print(event)

    def analyze_trades(self):
        """Analyze trading activity"""
        print(f"\n{Fore.CYAN}=== Trading Analysis ==={Style.RESET_ALL}")

        lines = self.read_log_file(self.dashboard_log)
        trades = []

        for line in lines:
            if "Trade action requested" in line:
                trades.append(line.strip())
            elif "Order placed successfully" in line:
                trades.append(line.strip())

        if not trades:
            print(f"{Fore.YELLOW}No trading activity found in logs{Style.RESET_ALL}")
            return

        print("\nTrading Activity:")
        for trade in trades:
            if "buy" in trade.lower():
                print(f"{Fore.GREEN}{trade}{Style.RESET_ALL}")
            elif "sell" in trade.lower():
                print(f"{Fore.RED}{trade}{Style.RESET_ALL}")
            else:
                print(trade)

    def analyze_metrics(self):
        """Analyze system metrics and performance"""
        print(f"\n{Fore.CYAN}=== Metrics Analysis ==={Style.RESET_ALL}")

        lines = self.read_log_file(self.dashboard_log)
        metrics = []

        for line in lines:
            if "Metrics updated" in line:
                try:
                    # Extract metrics JSON
                    metrics_json = re.search(r"Metrics updated: ({.*})", line)
                    if metrics_json:
                        metrics.append(json.loads(metrics_json.group(1)))
                except:
                    continue

        if not metrics:
            print(f"{Fore.YELLOW}No metrics data found in logs{Style.RESET_ALL}")
            return

        # Convert to DataFrame for analysis
        df = pd.DataFrame(metrics)

        print("\nMetrics Summary:")
        print(f"Total Trades: {df['total_trades'].iloc[-1]}")
        print(f"Winning Trades: {df['winning_trades'].iloc[-1]}")
        print(f"Losing Trades: {df['losing_trades'].iloc[-1]}")
        print(f"Total PnL: {df['total_pnl'].iloc[-1]:.2f}")
        print(f"Win Rate: {df['win_rate'].iloc[-1]*100:.2f}%")

    def analyze_ohlcv(self):
        """Analyze OHLCV data fetching"""
        print(f"\n{Fore.CYAN}=== OHLCV Data Analysis ==={Style.RESET_ALL}")

        lines = self.read_log_file(self.dashboard_log)
        ohlcv_events = []

        for line in lines:
            if "OHLCV Data Request" in line or "Fetched" in line:
                ohlcv_events.append(line.strip())

        if not ohlcv_events:
            print(f"{Fore.YELLOW}No OHLCV data fetching found in logs{Style.RESET_ALL}")
            return

        print("\nOHLCV Data Fetching Events:")
        for event in ohlcv_events:
            if "Fetched" in event:
                print(f"{Fore.GREEN}{event}{Style.RESET_ALL}")
            else:
                print(event)

    def run_full_analysis(self):
        """Run all analyses"""
        print(f"{Fore.CYAN}=== Starting Log Analysis ==={Style.RESET_ALL}")
        print(f"Analyzing logs from: {self.logs_dir}")

        self.analyze_errors()
        self.analyze_bot_status()
        self.analyze_trades()
        self.analyze_metrics()
        self.analyze_ohlcv()

        print(f"\n{Fore.CYAN}=== Analysis Complete ==={Style.RESET_ALL}")


def main():
    analyzer = LogAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
