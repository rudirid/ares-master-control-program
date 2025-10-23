"""
Enhanced Live Trading GUI Demo

Shows detailed AI analysis of fake news articles with realistic recommendations.

Features:
- Realistic ASX announcements
- Detailed sentiment analysis breakdown
- Filter decision explanations
- Simulated P&L tracking
- Real-time statistics

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
from typing import Dict, List
import random

import config


class EnhancedTradingGUI:
    """Enhanced GUI with detailed AI analysis."""

    def __init__(self, master, duration_minutes: int = 30):
        """Initialize enhanced GUI."""
        self.master = master
        self.duration_minutes = duration_minutes
        self.running = False
        self.start_time = None
        self.cycle = 0

        # Fake announcements with realistic details
        self.fake_announcements = [
            {
                'ticker': 'BHP',
                'title': 'Quarterly Production Report - Iron Ore output exceeds expectations',
                'content': 'BHP Group reports Q3 iron ore production of 71.2Mt, 8% above market consensus. Copper production also beat guidance at 475kt.',
                'expected_sentiment': 'POSITIVE',
                'keywords': ['exceeds', 'beat', 'above'],
                'materiality': 'HIGH',
                'realistic_price': 43.21
            },
            {
                'ticker': 'CBA',
                'title': 'Trading Update - Net Interest Margin under pressure',
                'content': 'Commonwealth Bank announces NIM compression of 5bps due to competitive lending environment. FY25 guidance maintained.',
                'expected_sentiment': 'NEGATIVE',
                'keywords': ['pressure', 'compression', 'competitive'],
                'materiality': 'HIGH',
                'realistic_price': 118.45
            },
            {
                'ticker': 'CSL',
                'title': 'Immunoglobulin Sales Surge in European Markets',
                'content': 'CSL reports 18% YoY growth in Ig sales across Europe. New facility in Switzerland ahead of schedule.',
                'expected_sentiment': 'POSITIVE',
                'keywords': ['surge', 'growth', 'ahead'],
                'materiality': 'HIGH',
                'realistic_price': 298.76
            },
            {
                'ticker': 'WES',
                'title': 'Wesfarmers warns of softening consumer demand',
                'content': 'Bunnings same-store sales down 2.3% in October. Kmart continues to perform strongly with 7% growth.',
                'expected_sentiment': 'MIXED',
                'keywords': ['warns', 'softening', 'down', 'strongly', 'growth'],
                'materiality': 'HIGH',
                'realistic_price': 68.92
            },
            {
                'ticker': 'FMG',
                'title': 'Fortescue achieves record shipment volumes',
                'content': 'Record quarterly shipments of 49Mt. Iron ore prices remain supportive. Green hydrogen division making progress.',
                'expected_sentiment': 'POSITIVE',
                'keywords': ['record', 'supportive', 'progress'],
                'materiality': 'HIGH',
                'realistic_price': 24.15
            },
            {
                'ticker': 'WOW',
                'title': 'Director Interest Notice - Appendix 3Y',
                'content': 'Director John Smith acquired 5,000 shares at $38.50.',
                'expected_sentiment': 'NEUTRAL',
                'keywords': [],
                'materiality': 'LOW',
                'realistic_price': 38.50
            },
            {
                'ticker': 'NAB',
                'title': 'Q2 FY25 Unaudited Cash Earnings decline 3%',
                'content': 'Cash earnings of $1.8B down 3% YoY. Credit quality remains strong with NPLs at 0.6%. Dividend maintained.',
                'expected_sentiment': 'NEGATIVE',
                'keywords': ['decline', 'down', 'remains strong', 'maintained'],
                'materiality': 'HIGH',
                'realistic_price': 35.22
            },
            {
                'ticker': 'RIO',
                'title': 'Rio Tinto announces $2B share buyback program',
                'content': 'Board approves $2B on-market buyback commencing immediately. Reflects strong cash position and outlook.',
                'expected_sentiment': 'POSITIVE',
                'keywords': ['buyback', 'strong', 'outlook'],
                'materiality': 'HIGH',
                'realistic_price': 122.85
            }
        ]

        # Statistics
        self.stats = {
            'announcements': 0,
            'recommendations': 0,
            'filtered': 0,
            'simulated_trades': [],
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0
        }

        self.setup_ui()

    def setup_ui(self):
        """Setup enhanced user interface."""
        self.master.title("Enhanced Live Trading Demo - AI Analysis")
        self.master.geometry("1600x1000")
        self.master.configure(bg='#1e1e1e')

        # Header
        header_frame = tk.Frame(self.master, bg='#2d2d2d', height=70)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Live Paper Trading - AI Analysis Demo",
            font=('Arial', 22, 'bold'),
            bg='#2d2d2d',
            fg='#00ff00'
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        self.status_label = tk.Label(
            header_frame,
            text="Status: Ready",
            font=('Arial', 12, 'bold'),
            bg='#2d2d2d',
            fg='#ffaa00'
        )
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=15)

        # Control panel
        control_frame = tk.Frame(self.master, bg='#2d2d2d')
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = tk.Button(
            control_frame,
            text=f"▶ Start Demo ({self.duration_minutes} min)",
            command=self.start_demo,
            bg='#00aa00',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=25,
            pady=12,
            relief=tk.RAISED,
            bd=3
        )
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = tk.Button(
            control_frame,
            text="■ Stop",
            command=self.stop_demo,
            bg='#aa0000',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=25,
            pady=12,
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        info_label = tk.Label(
            control_frame,
            text="Simulated announcements will appear every 30-60 seconds | Paper trading only - NO REAL MONEY",
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#ffaa00'
        )
        info_label.pack(side=tk.LEFT, padx=20, pady=5)

        # Main content
        content_frame = tk.Frame(self.master, bg='#1e1e1e')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Stats (narrower)
        left_panel = tk.Frame(content_frame, bg='#2d2d2d', width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_panel.pack_propagate(False)

        self.create_stats_panel(left_panel)

        # Right panel - Activity log (wider)
        right_panel = tk.Frame(content_frame, bg='#2d2d2d')
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_title = tk.Label(
            right_panel,
            text="AI Analysis & Trade Activity",
            font=('Arial', 16, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        log_title.pack(pady=(10, 5))

        # Activity log with larger font
        self.activity_log = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            width=100,
            height=35,
            bg='#0d0d0d',
            fg='#00ff00',
            font=('Consolas', 11),
            insertbackground='white',
            padx=10,
            pady=10
        )
        self.activity_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Configure tags for colors
        self.activity_log.tag_config('header', foreground='#00ffff', font=('Consolas', 11, 'bold'))
        self.activity_log.tag_config('green', foreground='#00ff00')
        self.activity_log.tag_config('yellow', foreground='#ffaa00')
        self.activity_log.tag_config('red', foreground='#ff4444')
        self.activity_log.tag_config('cyan', foreground='#00ffff')
        self.activity_log.tag_config('white', foreground='#ffffff')
        self.activity_log.tag_config('magenta', foreground='#ff00ff')

        # Bottom panel - Trades table
        self.create_trades_panel()

        # Initial message
        self.log("="*100, 'cyan')
        self.log("ENHANCED LIVE TRADING DEMO - AI ANALYSIS", 'header')
        self.log("="*100, 'cyan')
        self.log("This demo simulates ASX announcements and shows detailed AI analysis.", 'white')
        self.log("You'll see: Sentiment analysis | Filter decisions | Trade recommendations | Simulated P&L", 'white')
        self.log("", 'white')
        self.log("Click 'Start Demo' to begin watching the AI analyze fake news articles.", 'yellow')
        self.log("="*100 + "\n", 'cyan')

    def create_stats_panel(self, parent):
        """Create statistics panel."""
        stats_title = tk.Label(
            parent,
            text="📊 Live Statistics",
            font=('Arial', 16, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        stats_title.pack(pady=(10, 15))

        self.announcements_label = self.create_stat(parent, "Announcements", "0", '#ffffff')
        self.recommendations_label = self.create_stat(parent, "Recommendations", "0", '#00ff00')
        self.filtered_label = self.create_stat(parent, "Filtered Out", "0", '#ff6666')
        self.pass_rate_label = self.create_stat(parent, "Pass Rate", "0%", '#ffaa00')

        self.add_separator(parent)

        self.total_pnl_label = self.create_stat(parent, "Total P&L", "$0.00", '#00ff00')
        self.win_rate_label = self.create_stat(parent, "Win Rate", "0%", '#ffffff')
        self.winners_label = self.create_stat(parent, "Winners", "0", '#00ff00')
        self.losers_label = self.create_stat(parent, "Losers", "0", '#ff6666')

        self.add_separator(parent)

        self.time_label = self.create_stat(parent, "Time Left", f"{self.duration_minutes}:00", '#ffaa00')

    def create_stat(self, parent, title, value, color):
        """Create a statistic display."""
        frame = tk.Frame(parent, bg='#2d2d2d')
        frame.pack(fill=tk.X, padx=15, pady=8)

        title_label = tk.Label(
            frame,
            text=title,
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#888888',
            anchor='w'
        )
        title_label.pack(side=tk.TOP, fill=tk.X)

        value_label = tk.Label(
            frame,
            text=value,
            font=('Arial', 20, 'bold'),
            bg='#2d2d2d',
            fg=color,
            anchor='w'
        )
        value_label.pack(side=tk.TOP, fill=tk.X)

        return value_label

    def add_separator(self, parent):
        """Add visual separator."""
        sep = tk.Frame(parent, bg='#444444', height=1)
        sep.pack(fill=tk.X, padx=15, pady=10)

    def create_trades_panel(self):
        """Create trades table panel."""
        trades_panel = tk.Frame(self.master, bg='#2d2d2d')
        trades_panel.pack(fill=tk.BOTH, padx=10, pady=(5, 10))

        title = tk.Label(
            trades_panel,
            text="Recent Simulated Trades (P&L assumes $1000 per trade)",
            font=('Arial', 14, 'bold'),
            bg='#2d2d2d',
            fg='#ffffff'
        )
        title.pack(pady=(10, 5))

        # Treeview
        tree_frame = tk.Frame(trades_panel, bg='#2d2d2d')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.trades_tree = ttk.Treeview(
            tree_frame,
            columns=('Time', 'Ticker', 'Action', 'Entry', 'Exit', 'Return', 'P&L', 'Conf'),
            show='headings',
            height=6
        )

        for col in ('Time', 'Ticker', 'Action', 'Entry', 'Exit', 'Return', 'P&L', 'Conf'):
            self.trades_tree.heading(col, text=col)

        self.trades_tree.column('Time', width=80, anchor='center')
        self.trades_tree.column('Ticker', width=70, anchor='center')
        self.trades_tree.column('Action', width=70, anchor='center')
        self.trades_tree.column('Entry', width=90, anchor='center')
        self.trades_tree.column('Exit', width=90, anchor='center')
        self.trades_tree.column('Return', width=90, anchor='center')
        self.trades_tree.column('P&L', width=100, anchor='center')
        self.trades_tree.column('Conf', width=80, anchor='center')

        self.trades_tree.pack(fill=tk.BOTH, expand=True)

        # Style
        style = ttk.Style()
        style.configure('Treeview', rowheight=25, background='#1a1a1a', foreground='white', fieldbackground='#1a1a1a', font=('Arial', 10))
        style.configure('Treeview.Heading', background='#333333', foreground='white', font=('Arial', 10, 'bold'))

    def log(self, message, color='green'):
        """Log message with color."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.activity_log.insert(tk.END, f"[{timestamp}] ", 'white')
        self.activity_log.insert(tk.END, f"{message}\n", color)
        self.activity_log.see(tk.END)
        self.activity_log.update()

    def start_demo(self):
        """Start demonstration."""
        self.running = True
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: RUNNING ●", fg='#00ff00')

        self.log("", 'white')
        self.log("="*100, 'cyan')
        self.log("DEMO STARTED - Watching for announcements...", 'header')
        self.log("="*100 + "\n", 'cyan')

        # Start demo loop
        thread = threading.Thread(target=self.demo_loop, daemon=True)
        thread.start()

        # Start timer
        self.update_timer()

    def stop_demo(self):
        """Stop demonstration."""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: STOPPED", fg='#ff6666')

        self.log("", 'white')
        self.log("="*100, 'cyan')
        self.log("DEMO STOPPED", 'header')
        self.show_summary()

    def demo_loop(self):
        """Main demo loop."""
        while self.running and datetime.now() < self.end_time:
            self.cycle += 1

            # Random announcement
            announcement = random.choice(self.fake_announcements)

            self.log("\n" + "="*100, 'cyan')
            self.log(f"CYCLE #{self.cycle} - NEW ANNOUNCEMENT DETECTED", 'header')
            self.log("="*100, 'cyan')

            self.stats['announcements'] += 1

            # Show announcement
            self.log(f"Company: {announcement['ticker']}", 'yellow')
            self.log(f"Title: {announcement['title']}", 'white')
            self.log(f"Content: {announcement['content']}", 'white')
            self.log("", 'white')

            # Analyze
            self.analyze_announcement(announcement)

            # Update stats
            self.update_stats()

            # Wait 30-60 seconds
            wait_time = random.randint(30, 60)
            time.sleep(wait_time)

        if self.running:
            self.stop_demo()

    def analyze_announcement(self, ann: Dict):
        """Analyze announcement with detailed breakdown."""
        self.log("AI ANALYSIS:", 'header')
        self.log("-"*100, 'cyan')

        # 1. Sentiment Analysis
        self.log("1. SENTIMENT ANALYSIS", 'yellow')

        sentiment = ann['expected_sentiment']
        if sentiment == 'POSITIVE':
            score = random.uniform(0.65, 0.85)
            confidence = random.uniform(0.6, 0.8)
        elif sentiment == 'NEGATIVE':
            score = random.uniform(-0.85, -0.65)
            confidence = random.uniform(0.6, 0.8)
        else:
            score = random.uniform(-0.2, 0.2)
            confidence = random.uniform(0.4, 0.6)

        self.log(f"   Keywords detected: {', '.join(ann['keywords']) if ann['keywords'] else 'None'}", 'white')
        self.log(f"   Sentiment: {sentiment} (Score: {score:.2f}, Confidence: {confidence:.2f})", 'green' if sentiment == 'POSITIVE' else 'red' if sentiment == 'NEGATIVE' else 'yellow')

        # 2. Materiality Filter
        self.log("", 'white')
        self.log("2. MATERIALITY FILTER", 'yellow')

        if ann['materiality'] == 'HIGH':
            self.log("   ✓ PASS - Material announcement (High impact news)", 'green')
            materiality_pass = True
        else:
            self.log("   ✗ FAIL - Low materiality (Administrative/routine)", 'red')
            materiality_pass = False
            self.stats['filtered'] += 1

        # 3. TIME Filter
        self.log("", 'white')
        self.log("3. TIME FILTER (Announcement Age)", 'yellow')
        age_minutes = random.uniform(1, 15)
        if age_minutes < 5:
            self.log(f"   ✓ PASS - Ultra-fresh ({age_minutes:.1f} minutes) - Maximum edge! +0.15 confidence", 'green')
            time_boost = 0.15
            time_pass = True
        elif age_minutes < 30:
            self.log(f"   ✓ PASS - Fresh ({age_minutes:.1f} minutes) - Strong edge. +0.05 confidence", 'green')
            time_boost = 0.05
            time_pass = True
        else:
            self.log(f"   ✗ FAIL - Too old ({age_minutes:.1f} minutes) - Already priced in", 'red')
            time_boost = 0
            time_pass = False
            self.stats['filtered'] += 1

        # 4. TIME-OF-DAY Filter
        self.log("", 'white')
        self.log("4. TIME-OF-DAY FILTER", 'yellow')
        current_hour = datetime.now().hour
        if 10 <= current_hour <= 14:
            self.log(f"   ✓ PASS - Optimal trading time ({current_hour}:00 AEST) - High liquidity. +0.05 confidence", 'green')
            tod_boost = 0.05
            tod_pass = True
        else:
            self.log(f"   ✗ FAIL - Suboptimal time ({current_hour}:00 AEST) - Low liquidity", 'red')
            tod_boost = 0
            tod_pass = False
            self.stats['filtered'] += 1

        # 5. Technical Analysis
        self.log("", 'white')
        self.log("5. TECHNICAL ANALYSIS (Soft Modifier)", 'yellow')
        tech_bullish = random.choice([True, False])
        if tech_bullish:
            tech_boost = random.uniform(0.05, 0.15)
            self.log(f"   Bullish signals detected. +{tech_boost:.2f} confidence boost", 'green')
        else:
            tech_boost = random.uniform(-0.15, -0.05)
            self.log(f"   Bearish signals detected. {tech_boost:.2f} confidence penalty", 'red')

        # 6. Decision
        self.log("", 'white')
        self.log("6. FINAL DECISION", 'yellow')

        if not materiality_pass or not time_pass or not tod_pass:
            self.log("   ✗ FILTERED OUT - Failed one or more filters", 'red')
            self.log("-"*100 + "\n", 'cyan')
            return

        # Calculate final confidence
        final_confidence = confidence + time_boost + tod_boost + tech_boost
        final_confidence = max(0.0, min(1.0, final_confidence))

        self.log(f"   Base confidence: {confidence:.2f}", 'white')
        self.log(f"   + TIME boost: +{time_boost:.2f}", 'white')
        self.log(f"   + TIME-OF-DAY boost: +{tod_boost:.2f}", 'white')
        self.log(f"   + Technical boost: {tech_boost:+.2f}", 'white')
        self.log(f"   = Final confidence: {final_confidence:.2f}", 'cyan')

        if final_confidence >= 0.6:
            action = 'BUY' if sentiment == 'POSITIVE' else 'SELL'
            price = ann['realistic_price']

            self.log("", 'white')
            self.log(f"   ✓ RECOMMENDATION: {action} {ann['ticker']} @ ${price:.2f} (Confidence: {final_confidence:.2f})", 'green')

            self.stats['recommendations'] += 1

            # Simulate trade
            self.simulate_trade(ann['ticker'], action, price, final_confidence)
        else:
            self.log(f"   ✗ CONFIDENCE TOO LOW ({final_confidence:.2f} < 0.60) - No trade", 'red')
            self.stats['filtered'] += 1

        self.log("-"*100 + "\n", 'cyan')

    def simulate_trade(self, ticker, action, entry_price, confidence):
        """Simulate trade execution and outcome."""
        # Win probability based on confidence
        win_prob = 0.35 + (confidence - 0.6) * 0.4  # 35-55% win rate

        if random.random() < win_prob:
            return_pct = random.uniform(0.5, 3.5)
            is_winner = True
        else:
            return_pct = random.uniform(-5.0, -0.5)
            is_winner = False

        if action == 'SELL':
            return_pct = -return_pct

        exit_price = entry_price * (1 + return_pct / 100)

        # $1000 position size
        pnl = 1000 * (return_pct / 100)

        self.stats['total_pnl'] += pnl
        if is_winner:
            self.stats['winning_trades'] += 1
        else:
            self.stats['losing_trades'] += 1

        # Add to table
        self.trades_tree.insert(
            '', 0,
            values=(
                datetime.now().strftime('%H:%M:%S'),
                ticker,
                action,
                f"${entry_price:.2f}",
                f"${exit_price:.2f}",
                f"{return_pct:+.2f}%",
                f"${pnl:+.2f}",
                f"{confidence:.2f}"
            ),
            tags=('profit' if is_winner else 'loss',)
        )

        self.trades_tree.tag_configure('profit', foreground='#00ff00', font=('Arial', 10, 'bold'))
        self.trades_tree.tag_configure('loss', foreground='#ff6666', font=('Arial', 10, 'bold'))

        # Limit to 12 rows
        if len(self.trades_tree.get_children()) > 12:
            self.trades_tree.delete(self.trades_tree.get_children()[-1])

        # Log result
        color = 'green' if is_winner else 'red'
        result = "WIN" if is_winner else "LOSS"
        self.log(f"   SIMULATED TRADE RESULT: {result} | Return: {return_pct:+.2f}% | P&L: ${pnl:+.2f}", color)

    def update_stats(self):
        """Update statistics display."""
        self.announcements_label.config(text=str(self.stats['announcements']))
        self.recommendations_label.config(text=str(self.stats['recommendations']))
        self.filtered_label.config(text=str(self.stats['filtered']))

        if self.stats['announcements'] > 0:
            pass_rate = (self.stats['recommendations'] / self.stats['announcements'] * 100)
            self.pass_rate_label.config(text=f"{pass_rate:.1f}%")

        pnl = self.stats['total_pnl']
        self.total_pnl_label.config(text=f"${pnl:+.2f}", fg='#00ff00' if pnl >= 0 else '#ff6666')

        total_trades = self.stats['winning_trades'] + self.stats['losing_trades']
        if total_trades > 0:
            win_rate = (self.stats['winning_trades'] / total_trades * 100)
            self.win_rate_label.config(text=f"{win_rate:.1f}%")

        self.winners_label.config(text=str(self.stats['winning_trades']))
        self.losers_label.config(text=str(self.stats['losing_trades']))

    def update_timer(self):
        """Update countdown timer."""
        if self.running and self.end_time:
            remaining = self.end_time - datetime.now()
            minutes = max(0, int(remaining.total_seconds() // 60))
            seconds = max(0, int(remaining.total_seconds() % 60))
            self.time_label.config(text=f"{minutes}:{seconds:02d}")
            self.master.after(1000, self.update_timer)

    def show_summary(self):
        """Show final summary."""
        self.log("="*100, 'cyan')
        self.log("FINAL SUMMARY", 'header')
        self.log("="*100, 'cyan')
        self.log(f"Total Announcements: {self.stats['announcements']}", 'white')
        self.log(f"Recommendations Generated: {self.stats['recommendations']}", 'green')
        self.log(f"Filtered Out: {self.stats['filtered']}", 'red')

        if self.stats['announcements'] > 0:
            pass_rate = (self.stats['recommendations'] / self.stats['announcements'] * 100)
            self.log(f"Pass Rate: {pass_rate:.1f}%", 'yellow')

        self.log("", 'white')
        total_trades = self.stats['winning_trades'] + self.stats['losing_trades']
        self.log(f"Total Trades: {total_trades}", 'white')
        self.log(f"Winners: {self.stats['winning_trades']}", 'green')
        self.log(f"Losers: {self.stats['losing_trades']}", 'red')

        if total_trades > 0:
            win_rate = (self.stats['winning_trades'] / total_trades * 100)
            self.log(f"Win Rate: {win_rate:.1f}%", 'yellow')

        pnl_color = 'green' if self.stats['total_pnl'] >= 0 else 'red'
        self.log(f"Total P&L: ${self.stats['total_pnl']:+.2f}", pnl_color)

        self.log("", 'white')
        self.log("="*100, 'cyan')
        self.log("NOTE: This is SIMULATED data for demonstration only.", 'yellow')
        self.log("Real trading results will vary. Always use proper risk management.", 'yellow')
        self.log("="*100 + "\n", 'cyan')


def main():
    """Main entry point."""
    root = tk.Tk()
    app = EnhancedTradingGUI(root, duration_minutes=30)
    root.mainloop()


if __name__ == '__main__':
    main()
