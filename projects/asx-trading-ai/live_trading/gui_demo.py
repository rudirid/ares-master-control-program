"""
Live Trading GUI Demo

Interactive dashboard for watching live paper trading in action.

Shows:
- Real-time announcements
- Recommendation generation
- Simulated profit/loss
- Live statistics

Author: Claude Code
Date: 2025-10-10
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import yfinance as yf

import config
from live_trading.announcement_monitor import ASXAnnouncementMonitor
from live_trading.live_recommendation_engine import LiveRecommendationEngine


class LiveTradingGUI:
    """
    GUI for live trading demonstration.
    """

    def __init__(self, master, duration_minutes: int = 30):
        """
        Initialize GUI.

        Args:
            master: Tkinter root window
            duration_minutes: How long to run demo
        """
        self.master = master
        self.duration_minutes = duration_minutes
        self.running = False
        self.start_time = None
        self.end_time = None

        # Components
        self.monitor = ASXAnnouncementMonitor(
            db_path=config.DATABASE_PATH,
            check_interval_seconds=10,  # 10s to capture 30-90s alpha window
            data_source='test'  # Use test mode for demo
        )
        self.engine = LiveRecommendationEngine(config.DATABASE_PATH)

        # Statistics
        self.stats = {
            'announcements': 0,
            'recommendations': 0,
            'simulated_trades': [],
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0
        }

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        self.master.title("Live Trading Demo - ASX Stock Trading AI")
        self.master.geometry("1400x900")
        self.master.configure(bg='#1e1e1e')

        # Header
        header_frame = tk.Frame(self.master, bg='#2d2d2d', height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Live Paper Trading Demonstration",
            font=('Arial', 20, 'bold'),
            bg='#2d2d2d',
            fg='#00ff00'
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        self.status_label = tk.Label(
            header_frame,
            text="Status: Ready",
            font=('Arial', 12),
            bg='#2d2d2d',
            fg='#ffaa00'
        )
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # Control buttons
        button_frame = tk.Frame(self.master, bg='#1e1e1e')
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = tk.Button(
            button_frame,
            text="Start Demo (30 min)",
            command=self.start_demo,
            bg='#00aa00',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            command=self.stop_demo,
            bg='#aa0000',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Main content area
        content_frame = tk.Frame(self.master, bg='#1e1e1e')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Statistics
        left_panel = tk.Frame(content_frame, bg='#2d2d2d', width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5), pady=0)
        left_panel.pack_propagate(False)

        # Stats labels
        stats_title = tk.Label(
            left_panel,
            text="Live Statistics",
            font=('Arial', 16, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        stats_title.pack(pady=(10, 20))

        self.announcements_label = self.create_stat_label(left_panel, "Announcements Detected", "0")
        self.recommendations_label = self.create_stat_label(left_panel, "Recommendations Generated", "0")
        self.pass_rate_label = self.create_stat_label(left_panel, "Filter Pass Rate", "0%")

        separator1 = tk.Frame(left_panel, bg='#444444', height=2)
        separator1.pack(fill=tk.X, padx=20, pady=10)

        self.total_pnl_label = self.create_stat_label(left_panel, "Total P&L (Simulated)", "$0.00", color='#00ff00')
        self.win_rate_label = self.create_stat_label(left_panel, "Win Rate", "0%")
        self.winning_trades_label = self.create_stat_label(left_panel, "Winning Trades", "0")
        self.losing_trades_label = self.create_stat_label(left_panel, "Losing Trades", "0")

        separator2 = tk.Frame(left_panel, bg='#444444', height=2)
        separator2.pack(fill=tk.X, padx=20, pady=10)

        self.time_label = self.create_stat_label(left_panel, "Time Remaining", f"{self.duration_minutes}:00")

        # Right panel - Activity log
        right_panel = tk.Frame(content_frame, bg='#2d2d2d')
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        log_title = tk.Label(
            right_panel,
            text="Live Activity Feed",
            font=('Arial', 16, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        log_title.pack(pady=(10, 10))

        # Activity log
        self.activity_log = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            width=80,
            height=30,
            bg='#1a1a1a',
            fg='#00ff00',
            font=('Consolas', 10),
            insertbackground='white'
        )
        self.activity_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Bottom panel - Recent trades
        bottom_panel = tk.Frame(self.master, bg='#2d2d2d')
        bottom_panel.pack(fill=tk.BOTH, padx=10, pady=(5, 10), expand=False)

        trades_title = tk.Label(
            bottom_panel,
            text="Recent Simulated Trades",
            font=('Arial', 14, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        trades_title.pack(pady=(10, 5))

        # Trades table
        trades_frame = tk.Frame(bottom_panel, bg='#2d2d2d')
        trades_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.trades_tree = ttk.Treeview(
            trades_frame,
            columns=('Ticker', 'Action', 'Entry', 'Exit', 'Return', 'P&L', 'Confidence'),
            show='headings',
            height=6
        )

        self.trades_tree.heading('Ticker', text='Ticker')
        self.trades_tree.heading('Action', text='Action')
        self.trades_tree.heading('Entry', text='Entry $')
        self.trades_tree.heading('Exit', text='Exit $')
        self.trades_tree.heading('Return', text='Return %')
        self.trades_tree.heading('P&L', text='P&L $')
        self.trades_tree.heading('Confidence', text='Confidence')

        self.trades_tree.column('Ticker', width=80, anchor='center')
        self.trades_tree.column('Action', width=80, anchor='center')
        self.trades_tree.column('Entry', width=100, anchor='center')
        self.trades_tree.column('Exit', width=100, anchor='center')
        self.trades_tree.column('Return', width=100, anchor='center')
        self.trades_tree.column('P&L', width=100, anchor='center')
        self.trades_tree.column('Confidence', width=100, anchor='center')

        self.trades_tree.pack(fill=tk.BOTH, expand=True)

        # Style
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', background='#1a1a1a', foreground='white', fieldbackground='#1a1a1a')
        style.configure('Treeview.Heading', background='#2d2d2d', foreground='white', font=('Arial', 10, 'bold'))

        # Initial log message
        self.log_message("System ready. Click 'Start Demo' to begin.", color='cyan')
        self.log_message(f"Demo will run for {self.duration_minutes} minutes with simulated announcements.", color='yellow')
        self.log_message("This is PAPER TRADING - no real money involved.\n", color='yellow')

    def create_stat_label(self, parent, title: str, value: str, color: str = '#ffffff'):
        """Create a statistic display label."""
        frame = tk.Frame(parent, bg='#2d2d2d')
        frame.pack(fill=tk.X, padx=20, pady=5)

        title_label = tk.Label(
            frame,
            text=title,
            font=('Arial', 11),
            bg='#2d2d2d',
            fg='#aaaaaa',
            anchor='w'
        )
        title_label.pack(side=tk.TOP, fill=tk.X)

        value_label = tk.Label(
            frame,
            text=value,
            font=('Arial', 18, 'bold'),
            bg='#2d2d2d',
            fg=color,
            anchor='w'
        )
        value_label.pack(side=tk.TOP, fill=tk.X)

        return value_label

    def log_message(self, message: str, color: str = 'green'):
        """Add message to activity log."""
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Color map
        color_map = {
            'green': '#00ff00',
            'yellow': '#ffaa00',
            'red': '#ff0000',
            'cyan': '#00ffff',
            'white': '#ffffff'
        }

        tag = f"tag_{color}"
        self.activity_log.tag_config(tag, foreground=color_map.get(color, '#00ff00'))

        self.activity_log.insert(tk.END, f"[{timestamp}] ", 'tag_white')
        self.activity_log.insert(tk.END, f"{message}\n", tag)
        self.activity_log.see(tk.END)
        self.activity_log.update()

    def start_demo(self):
        """Start the demo."""
        self.running = True
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: RUNNING", fg='#00ff00')

        self.log_message("="*80, color='cyan')
        self.log_message("LIVE TRADING DEMO STARTED", color='cyan')
        self.log_message("="*80, color='cyan')
        self.log_message(f"Duration: {self.duration_minutes} minutes", color='white')
        self.log_message(f"Using: TEST MODE (simulated announcements)", color='white')
        self.log_message("", color='white')

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.run_demo_loop, daemon=True)
        self.monitor_thread.start()

        # Start timer update
        self.update_timer()

    def stop_demo(self):
        """Stop the demo."""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: STOPPED", fg='#ff0000')

        self.log_message("\n" + "="*80, color='cyan')
        self.log_message("DEMO STOPPED BY USER", color='yellow')
        self.log_message("="*80, color='cyan')
        self.display_final_summary()

    def run_demo_loop(self):
        """Main demo loop."""
        cycle = 0

        while self.running and datetime.now() < self.end_time:
            cycle += 1

            self.log_message(f"\n{'='*80}", color='cyan')
            self.log_message(f"CYCLE #{cycle}", color='cyan')
            self.log_message(f"{'='*80}", color='cyan')

            # Fetch announcements
            announcements = self.monitor.fetch_announcements()

            if announcements:
                self.stats['announcements'] += len(announcements)
                self.log_message(f"Found {len(announcements)} announcements", color='white')

                # Store and process
                for announcement in announcements:
                    if self.monitor.store_announcement(announcement):
                        self.log_message(
                            f"  NEW: {announcement['ticker']} - {announcement['title']}",
                            color='yellow'
                        )

                # Process unprocessed
                recommendations = self.engine.process_unprocessed_announcements()

                if recommendations:
                    self.stats['recommendations'] += len(recommendations)

                    for rec in recommendations:
                        self.log_message(
                            f"  RECOMMENDATION: {rec['recommendation']} {rec['ticker']} "
                            f"@ ${rec['entry_price']:.2f} (Conf: {rec['confidence']:.2f})",
                            color='green'
                        )

                        # Simulate trade
                        self.simulate_trade(rec)
                else:
                    self.log_message("  All announcements filtered (no tradeable signals)", color='red')
            else:
                self.log_message("No announcements this cycle", color='white')

            # Update UI
            self.update_stats()

            # Wait before next cycle
            time.sleep(10)  # Check every 10 seconds - captures 30-90s alpha window

        if self.running:
            # Time expired
            self.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: COMPLETE", fg='#ffaa00')

            self.log_message("\n" + "="*80, color='cyan')
            self.log_message("DEMO COMPLETE (TIME LIMIT REACHED)", color='yellow')
            self.log_message("="*80, color='cyan')
            self.display_final_summary()

    def simulate_trade(self, recommendation: Dict):
        """
        Simulate a trade with random outcome.

        In real trading, this would execute and track actual positions.
        For demo, we simulate immediate outcome.
        """
        ticker = recommendation['ticker']
        action = recommendation['recommendation']
        entry_price = recommendation['entry_price']
        confidence = recommendation['confidence']

        # Simulate exit price (random but biased by confidence)
        # Higher confidence = higher chance of profit
        profit_probability = 0.3 + (confidence - 0.6) * 0.5  # 30-55% win rate

        if random.random() < profit_probability:
            # Winner
            return_pct = random.uniform(0.5, 3.0)  # 0.5% to 3% gain
            is_winner = True
        else:
            # Loser
            return_pct = random.uniform(-5.0, -0.5)  # -5% to -0.5% loss (stop loss)
            is_winner = False

        if action == 'SELL':
            return_pct = -return_pct  # Invert for short positions

        exit_price = entry_price * (1 + return_pct / 100)

        # Calculate P&L (assuming $1000 position size)
        position_size = 1000
        pnl = position_size * (return_pct / 100)

        # Update stats
        self.stats['total_pnl'] += pnl
        if is_winner:
            self.stats['winning_trades'] += 1
        else:
            self.stats['losing_trades'] += 1

        # Add to trades list
        trade = {
            'ticker': ticker,
            'action': action,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': return_pct,
            'pnl': pnl,
            'confidence': confidence
        }
        self.stats['simulated_trades'].append(trade)

        # Add to trades table
        self.add_trade_to_table(trade)

        # Log result
        color = 'green' if is_winner else 'red'
        self.log_message(
            f"  SIMULATED TRADE: {action} {ticker} | "
            f"Entry: ${entry_price:.2f} | Exit: ${exit_price:.2f} | "
            f"Return: {return_pct:+.2f}% | P&L: ${pnl:+.2f}",
            color=color
        )

    def add_trade_to_table(self, trade: Dict):
        """Add trade to the trades table."""
        color_tag = 'profit' if trade['pnl'] > 0 else 'loss'

        self.trades_tree.insert(
            '',
            0,  # Insert at top
            values=(
                trade['ticker'],
                trade['action'],
                f"${trade['entry_price']:.2f}",
                f"${trade['exit_price']:.2f}",
                f"{trade['return_pct']:+.2f}%",
                f"${trade['pnl']:+.2f}",
                f"{trade['confidence']:.2f}"
            ),
            tags=(color_tag,)
        )

        # Color code
        self.trades_tree.tag_configure('profit', foreground='#00ff00')
        self.trades_tree.tag_configure('loss', foreground='#ff6666')

        # Limit to 10 trades
        if len(self.trades_tree.get_children()) > 10:
            self.trades_tree.delete(self.trades_tree.get_children()[-1])

    def update_stats(self):
        """Update statistics display."""
        # Basic stats
        self.announcements_label.config(text=str(self.stats['announcements']))
        self.recommendations_label.config(text=str(self.stats['recommendations']))

        pass_rate = (self.stats['recommendations'] / self.stats['announcements'] * 100) if self.stats['announcements'] > 0 else 0
        self.pass_rate_label.config(text=f"{pass_rate:.1f}%")

        # P&L
        total_pnl = self.stats['total_pnl']
        pnl_color = '#00ff00' if total_pnl >= 0 else '#ff0000'
        self.total_pnl_label.config(text=f"${total_pnl:+.2f}", fg=pnl_color)

        # Win rate
        total_trades = self.stats['winning_trades'] + self.stats['losing_trades']
        win_rate = (self.stats['winning_trades'] / total_trades * 100) if total_trades > 0 else 0
        self.win_rate_label.config(text=f"{win_rate:.1f}%")

        self.winning_trades_label.config(text=str(self.stats['winning_trades']))
        self.losing_trades_label.config(text=str(self.stats['losing_trades']))

    def update_timer(self):
        """Update countdown timer."""
        if self.running and self.end_time:
            remaining = self.end_time - datetime.now()
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            self.time_label.config(text=f"{minutes}:{seconds:02d}")

            self.master.after(1000, self.update_timer)

    def display_final_summary(self):
        """Display final summary."""
        self.log_message("\nFINAL SUMMARY:", color='cyan')
        self.log_message(f"Total Announcements: {self.stats['announcements']}", color='white')
        self.log_message(f"Total Recommendations: {self.stats['recommendations']}", color='white')

        pass_rate = (self.stats['recommendations'] / self.stats['announcements'] * 100) if self.stats['announcements'] > 0 else 0
        self.log_message(f"Filter Pass Rate: {pass_rate:.1f}%", color='white')

        self.log_message("", color='white')
        self.log_message(f"Total Simulated Trades: {len(self.stats['simulated_trades'])}", color='white')
        self.log_message(f"Winning Trades: {self.stats['winning_trades']}", color='green')
        self.log_message(f"Losing Trades: {self.stats['losing_trades']}", color='red')

        total_trades = self.stats['winning_trades'] + self.stats['losing_trades']
        if total_trades > 0:
            win_rate = (self.stats['winning_trades'] / total_trades * 100)
            self.log_message(f"Win Rate: {win_rate:.1f}%", color='cyan')

        pnl_color = 'green' if self.stats['total_pnl'] >= 0 else 'red'
        self.log_message(f"Total P&L: ${self.stats['total_pnl']:+.2f}", color=pnl_color)

        self.log_message("\n" + "="*80, color='cyan')
        self.log_message("NOTE: This is simulated data for demonstration purposes.", color='yellow')
        self.log_message("Real trading results will vary. Always use proper risk management.", color='yellow')


def main():
    """Main entry point."""
    root = tk.Tk()
    app = LiveTradingGUI(root, duration_minutes=30)
    root.mainloop()


if __name__ == '__main__':
    main()
