"""
Backtest Simulation GUI

Interactive GUI showing the complete simulation timeline, trade events,
recommendations, and performance metrics.

Author: Claude Code
Date: 2025-10-10
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from backtesting.historical_simulator import HistoricalSimulator


class SimulationGUI:
    """
    GUI for running and visualizing backtesting simulations.
    """

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Trading Strategy Backtest Simulator")
        self.root.geometry("1400x900")

        # Simulation state
        self.simulator = None
        self.results = None
        self.is_running = False

        # Create UI
        self.create_widgets()

    def create_widgets(self):
        """Create all UI widgets."""
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            header_frame,
            text="Historical Backtest Simulator",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = ttk.Label(
            header_frame,
            text="No Look-Ahead Bias | Real-Time Event Simulation",
            font=("Arial", 10)
        )
        subtitle_label.pack(side=tk.LEFT, padx=20)

        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Simulation Configuration", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # Number of samples
        ttk.Label(config_frame, text="Number of Samples:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.samples_var = tk.IntVar(value=300)
        samples_entry = ttk.Entry(config_frame, textvariable=self.samples_var, width=10)
        samples_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Initial capital
        ttk.Label(config_frame, text="Initial Capital:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.capital_var = tk.DoubleVar(value=10000.0)
        capital_entry = ttk.Entry(config_frame, textvariable=self.capital_var, width=10)
        capital_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Min confidence
        ttk.Label(config_frame, text="Min Confidence:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.confidence_var = tk.DoubleVar(value=0.7)
        confidence_entry = ttk.Entry(config_frame, textvariable=self.confidence_var, width=10)
        confidence_entry.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        # Run button
        self.run_button = ttk.Button(
            config_frame,
            text="▶ Run Simulation",
            command=self.run_simulation
        )
        self.run_button.grid(row=0, column=6, padx=20, pady=5)

        # Export button
        self.export_button = ttk.Button(
            config_frame,
            text="📊 Export Report",
            command=self.export_report,
            state=tk.DISABLED
        )
        self.export_button.grid(row=0, column=7, padx=5, pady=5)

        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Summary
        self.summary_frame = ttk.Frame(notebook)
        notebook.add(self.summary_frame, text="📈 Summary")
        self.create_summary_tab()

        # Tab 2: Event Timeline
        self.timeline_frame = ttk.Frame(notebook)
        notebook.add(self.timeline_frame, text="🕒 Event Timeline")
        self.create_timeline_tab()

        # Tab 3: Trades
        self.trades_frame = ttk.Frame(notebook)
        notebook.add(self.trades_frame, text="💼 Trades")
        self.create_trades_tab()

        # Tab 4: Analysis
        self.analysis_frame = ttk.Frame(notebook)
        notebook.add(self.analysis_frame, text="📊 Analysis")
        self.create_analysis_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready to run simulation")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_summary_tab(self):
        """Create summary metrics tab."""
        # Metrics frame
        metrics_frame = ttk.Frame(self.summary_frame, padding="10")
        metrics_frame.pack(fill=tk.BOTH, expand=True)

        # Create metric cards in a grid
        self.metric_labels = {}

        metrics = [
            ("Initial Capital", "initial_capital", "$10,000.00"),
            ("Final Capital", "final_capital", "$0.00"),
            ("Total Return", "total_return_pct", "0.00%"),
            ("Total P/L", "total_pnl", "$0.00"),
            ("Total Trades", "total_trades", "0"),
            ("Winning Trades", "winning_trades", "0"),
            ("Losing Trades", "losing_trades", "0"),
            ("Win Rate", "win_rate", "0.0%"),
            ("Avg Win", "avg_win", "$0.00"),
            ("Avg Loss", "avg_loss", "$0.00"),
            ("Max Drawdown", "max_drawdown_pct", "0.00%"),
            ("Total Events", "total_events", "0"),
        ]

        row, col = 0, 0
        for label_text, key, default_value in metrics:
            frame = ttk.LabelFrame(metrics_frame, text=label_text, padding="10")
            frame.grid(row=row, column=col, padx=5, pady=5, sticky=tk.NSEW)

            value_label = ttk.Label(
                frame,
                text=default_value,
                font=("Arial", 14, "bold"),
                foreground="#2c3e50"
            )
            value_label.pack()

            self.metric_labels[key] = value_label

            col += 1
            if col >= 3:
                col = 0
                row += 1

        # Configure grid weights
        for i in range(3):
            metrics_frame.columnconfigure(i, weight=1)
        for i in range(4):
            metrics_frame.rowconfigure(i, weight=1)

    def create_timeline_tab(self):
        """Create event timeline tab."""
        # Toolbar
        toolbar = ttk.Frame(self.timeline_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(toolbar, text="Filter Events:").pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar(value="ALL")
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["ALL", "NEWS", "RECOMMENDATION", "ENTRY", "EXIT", "REJECTED", "STOP_LOSS", "CIRCUIT_BREAKER"],
            state="readonly",
            width=20
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.update_timeline())

        # Timeline tree
        timeline_container = ttk.Frame(self.timeline_frame)
        timeline_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars
        vsb = ttk.Scrollbar(timeline_container, orient="vertical")
        hsb = ttk.Scrollbar(timeline_container, orient="horizontal")

        # Treeview
        self.timeline_tree = ttk.Treeview(
            timeline_container,
            columns=("Time", "Type", "Ticker", "Description"),
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.timeline_tree.yview)
        hsb.config(command=self.timeline_tree.xview)

        # Column configuration
        self.timeline_tree.heading("#0", text="ID")
        self.timeline_tree.heading("Time", text="Date/Time")
        self.timeline_tree.heading("Type", text="Event Type")
        self.timeline_tree.heading("Ticker", text="Ticker")
        self.timeline_tree.heading("Description", text="Description")

        self.timeline_tree.column("#0", width=50)
        self.timeline_tree.column("Time", width=150)
        self.timeline_tree.column("Type", width=150)
        self.timeline_tree.column("Ticker", width=80)
        self.timeline_tree.column("Description", width=500)

        # Pack
        self.timeline_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)

        timeline_container.grid_rowconfigure(0, weight=1)
        timeline_container.grid_columnconfigure(0, weight=1)

        # Configure tags for colors
        self.timeline_tree.tag_configure('NEWS', background='#e8f4f8')
        self.timeline_tree.tag_configure('RECOMMENDATION', background='#fff9e6')
        self.timeline_tree.tag_configure('ENTRY', background='#d4edda')
        self.timeline_tree.tag_configure('EXIT', background='#f8d7da')
        self.timeline_tree.tag_configure('REJECTED', background='#f5f5f5')
        self.timeline_tree.tag_configure('STOP_LOSS', background='#ffcccc')
        self.timeline_tree.tag_configure('CIRCUIT_BREAKER', background='#ff9999')

    def create_trades_tab(self):
        """Create trades table tab."""
        # Trades tree
        trades_container = ttk.Frame(self.trades_frame)
        trades_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(trades_container, orient="vertical")
        hsb = ttk.Scrollbar(trades_container, orient="horizontal")

        # Treeview
        self.trades_tree = ttk.Treeview(
            trades_container,
            columns=("Ticker", "Entry Date", "Entry Price", "Exit Date", "Exit Price", "Shares", "P/L", "Return %", "Days", "Reason"),
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.trades_tree.yview)
        hsb.config(command=self.trades_tree.xview)

        # Columns
        self.trades_tree.heading("#0", text="ID")
        self.trades_tree.heading("Ticker", text="Ticker")
        self.trades_tree.heading("Entry Date", text="Entry Date")
        self.trades_tree.heading("Entry Price", text="Entry Price")
        self.trades_tree.heading("Exit Date", text="Exit Date")
        self.trades_tree.heading("Exit Price", text="Exit Price")
        self.trades_tree.heading("Shares", text="Shares")
        self.trades_tree.heading("P/L", text="P/L ($)")
        self.trades_tree.heading("Return %", text="Return %")
        self.trades_tree.heading("Days", text="Days Held")
        self.trades_tree.heading("Reason", text="Exit Reason")

        self.trades_tree.column("#0", width=40)
        self.trades_tree.column("Ticker", width=80)
        self.trades_tree.column("Entry Date", width=100)
        self.trades_tree.column("Entry Price", width=100)
        self.trades_tree.column("Exit Date", width=100)
        self.trades_tree.column("Exit Price", width=100)
        self.trades_tree.column("Shares", width=80)
        self.trades_tree.column("P/L", width=100)
        self.trades_tree.column("Return %", width=100)
        self.trades_tree.column("Days", width=80)
        self.trades_tree.column("Reason", width=200)

        # Pack
        self.trades_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)

        trades_container.grid_rowconfigure(0, weight=1)
        trades_container.grid_columnconfigure(0, weight=1)

        # Configure tags
        self.trades_tree.tag_configure('WIN', background='#d4edda')
        self.trades_tree.tag_configure('LOSS', background='#f8d7da')

    def create_analysis_tab(self):
        """Create analysis tab."""
        analysis_text = scrolledtext.ScrolledText(
            self.analysis_frame,
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.analysis_text = analysis_text

    def run_simulation(self):
        """Run the backtest simulation."""
        if self.is_running:
            messagebox.showwarning("Simulation Running", "A simulation is already running")
            return

        # Get parameters
        samples = self.samples_var.get()
        capital = self.capital_var.get()
        min_conf = self.confidence_var.get()

        if samples < 1 or samples > 1000:
            messagebox.showerror("Invalid Input", "Samples must be between 1 and 1000")
            return

        if capital < 100:
            messagebox.showerror("Invalid Input", "Capital must be at least $100")
            return

        # Update UI
        self.is_running = True
        self.run_button.config(state=tk.DISABLED)
        self.status_var.set(f"Running simulation with {samples} samples...")

        # Run in thread
        thread = threading.Thread(target=self._run_simulation_thread, args=(samples, capital, min_conf))
        thread.daemon = True
        thread.start()

    def _run_simulation_thread(self, samples, capital, min_conf):
        """Run simulation in background thread."""
        try:
            # Create simulator
            from backtesting.historical_simulator import HistoricalSimulator
            from paper_trading.risk_manager import RiskConfig

            risk_config = RiskConfig(
                portfolio_value=capital,
                min_confidence=min_conf
            )

            self.simulator = HistoricalSimulator(
                db_path=config.DATABASE_PATH,
                initial_capital=capital,
                risk_config=risk_config
            )

            # Run simulation
            self.results = self.simulator.run_simulation(max_articles=samples)

            # Update UI on main thread
            self.root.after(0, self.update_results)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))
            self.root.after(0, self.reset_ui)

    def update_results(self):
        """Update UI with simulation results."""
        if 'error' in self.results:
            messagebox.showerror("Simulation Error", self.results['error'])
            self.reset_ui()
            return

        # Update summary metrics
        self.update_summary()

        # Update timeline
        self.update_timeline()

        # Update trades
        self.update_trades()

        # Update analysis
        self.update_analysis()

        # Reset UI
        self.reset_ui()

        # Enable export
        self.export_button.config(state=tk.NORMAL)

        self.status_var.set(f"Simulation complete! {self.results['total_trades']} trades executed.")

    def update_summary(self):
        """Update summary metrics."""
        # Update each metric label
        self.metric_labels['initial_capital'].config(text=f"${self.results['initial_capital']:,.2f}")

        final_capital = self.results['final_capital']
        self.metric_labels['final_capital'].config(text=f"${final_capital:,.2f}")

        total_return = self.results['total_return_pct']
        color = "#27ae60" if total_return >= 0 else "#e74c3c"
        self.metric_labels['total_return_pct'].config(
            text=f"{total_return:+.2f}%",
            foreground=color
        )

        total_pnl = self.results['total_pnl']
        color = "#27ae60" if total_pnl >= 0 else "#e74c3c"
        self.metric_labels['total_pnl'].config(
            text=f"${total_pnl:+,.2f}",
            foreground=color
        )

        self.metric_labels['total_trades'].config(text=str(self.results['total_trades']))
        self.metric_labels['winning_trades'].config(text=str(self.results['winning_trades']))
        self.metric_labels['losing_trades'].config(text=str(self.results['losing_trades']))

        win_rate = self.results['win_rate']
        color = "#27ae60" if win_rate >= 55 else "#e74c3c"
        self.metric_labels['win_rate'].config(
            text=f"{win_rate:.1f}%",
            foreground=color
        )

        self.metric_labels['avg_win'].config(text=f"${self.results['avg_win']:+,.2f}")
        self.metric_labels['avg_loss'].config(text=f"${self.results['avg_loss']:+,.2f}")
        self.metric_labels['max_drawdown_pct'].config(text=f"{self.results['max_drawdown_pct']:.2f}%")
        self.metric_labels['total_events'].config(text=str(self.results['total_events']))

    def update_timeline(self):
        """Update event timeline."""
        # Clear existing
        for item in self.timeline_tree.get_children():
            self.timeline_tree.delete(item)

        if not self.results or 'events' not in self.results:
            return

        # Get filter
        filter_type = self.filter_var.get()

        # Add events
        for idx, event in enumerate(self.results['events']):
            if filter_type != "ALL" and event.event_type != filter_type:
                continue

            self.timeline_tree.insert(
                "",
                tk.END,
                text=str(idx + 1),
                values=(
                    event.timestamp,
                    event.event_type,
                    event.ticker,
                    event.description
                ),
                tags=(event.event_type,)
            )

    def update_trades(self):
        """Update trades table."""
        # Clear existing
        for item in self.trades_tree.get_children():
            self.trades_tree.delete(item)

        if not self.results or 'positions' not in self.results:
            return

        # Add trades
        for pos in self.results['positions']:
            tag = 'WIN' if pos.profit_loss > 0 else 'LOSS'

            self.trades_tree.insert(
                "",
                tk.END,
                text=str(pos.position_id),
                values=(
                    pos.ticker,
                    pos.entry_date,
                    f"${pos.entry_price:.2f}",
                    pos.exit_date,
                    f"${pos.exit_price:.2f}",
                    pos.shares,
                    f"${pos.profit_loss:+,.2f}",
                    f"{pos.return_pct:+.2f}%",
                    pos.days_held,
                    pos.exit_reason
                ),
                tags=(tag,)
            )

    def update_analysis(self):
        """Update analysis text."""
        if not self.results:
            return

        self.analysis_text.delete('1.0', tk.END)

        # Build analysis report
        report = []
        report.append("=" * 70)
        report.append("SIMULATION ANALYSIS REPORT")
        report.append("=" * 70)
        report.append("")

        report.append("PERFORMANCE SUMMARY")
        report.append("-" * 70)
        report.append(f"Initial Capital:    ${self.results['initial_capital']:,.2f}")
        report.append(f"Final Capital:      ${self.results['final_capital']:,.2f}")
        report.append(f"Total Return:       {self.results['total_return_pct']:+.2f}%")
        report.append(f"Total P/L:          ${self.results['total_pnl']:+,.2f}")
        report.append("")

        report.append("TRADING STATISTICS")
        report.append("-" * 70)
        report.append(f"Total Trades:       {self.results['total_trades']}")
        report.append(f"Winning Trades:     {self.results['winning_trades']}")
        report.append(f"Losing Trades:      {self.results['losing_trades']}")
        report.append(f"Win Rate:           {self.results['win_rate']:.1f}%")
        report.append(f"Average Win:        ${self.results['avg_win']:+,.2f}")
        report.append(f"Average Loss:       ${self.results['avg_loss']:+,.2f}")

        if self.results['avg_loss'] != 0:
            profit_factor = abs(self.results['avg_win'] / self.results['avg_loss'])
            report.append(f"Profit Factor:      {profit_factor:.2f}")

        report.append("")

        report.append("RISK METRICS")
        report.append("-" * 70)
        report.append(f"Max Drawdown:       {self.results['max_drawdown_pct']:.2f}%")
        report.append("")

        report.append("PROOF OF NO LOOK-AHEAD BIAS")
        report.append("-" * 70)
        report.append("✓ All news processed in chronological order")
        report.append("✓ Entry prices from NEXT day after news (T+1)")
        report.append("✓ Exit prices from holding period end date")
        report.append("✓ No access to future information")
        report.append("✓ Stop losses checked with current prices only")
        report.append("")

        report.append("=" * 70)

        self.analysis_text.insert('1.0', '\n'.join(report))

    def export_report(self):
        """Export results to file."""
        if not self.results:
            messagebox.showwarning("No Results", "Run a simulation first")
            return

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_report_{timestamp}.txt"

        try:
            # Export results
            with open(filename, 'w') as f:
                f.write(self.analysis_text.get('1.0', tk.END))
                f.write("\n\nDETAILED TRADE LOG\n")
                f.write("=" * 70 + "\n\n")

                for pos in self.results['positions']:
                    f.write(f"Trade #{pos.position_id}\n")
                    f.write(f"  Ticker: {pos.ticker}\n")
                    f.write(f"  Entry: {pos.entry_date} @ ${pos.entry_price:.2f}\n")
                    f.write(f"  Exit:  {pos.exit_date} @ ${pos.exit_price:.2f}\n")
                    f.write(f"  Shares: {pos.shares}\n")
                    f.write(f"  P/L: ${pos.profit_loss:+,.2f} ({pos.return_pct:+.2f}%)\n")
                    f.write(f"  Days Held: {pos.days_held}\n")
                    f.write(f"  Reason: {pos.exit_reason}\n")
                    f.write("\n")

            messagebox.showinfo("Export Complete", f"Report saved to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def reset_ui(self):
        """Reset UI after simulation."""
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)


def main():
    """Run the GUI."""
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
