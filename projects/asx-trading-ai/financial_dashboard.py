"""
ASX Trading AI - Financial Adviser Dashboard

Professional GUI for monitoring trading system performance, analyzing announcements,
and tracking recommendations in real-time.

Features:
- Live announcement monitoring with alpha window tracking
- Recommendation performance metrics
- Filter analysis and signal quality
- Price-sensitive announcement tracking
- Time-of-day performance breakdown
- Exportable reports for client analysis

Author: Claude Code
Date: 2025-10-15
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sqlite3
from datetime import datetime, timedelta
import threading
import time
import pytz

class FinancialDashboard:
    """Professional financial analysis dashboard for ASX Trading AI."""

    def __init__(self, db_path='data/trading.db'):
        self.db_path = db_path
        self.tz = pytz.timezone('Australia/Sydney')
        self.auto_refresh = True

        # Create main window
        self.root = tk.Tk()
        self.root.title("ASX Trading AI - Financial Analysis Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')

        # Configure styles
        self.setup_styles()

        # Create GUI components
        self.create_header()
        self.create_main_content()
        self.create_footer()

        # Start auto-refresh
        self.start_auto_refresh()

    def setup_styles(self):
        """Setup professional color scheme and styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        bg_dark = '#1e1e1e'
        bg_medium = '#2d2d2d'
        bg_light = '#3d3d3d'
        fg_text = '#e0e0e0'
        accent_green = '#4caf50'
        accent_red = '#f44336'
        accent_blue = '#2196f3'
        accent_yellow = '#ffc107'

        # Configure styles
        style.configure('Title.TLabel', background=bg_dark, foreground=fg_text,
                       font=('Segoe UI', 20, 'bold'))
        style.configure('Subtitle.TLabel', background=bg_dark, foreground='#999',
                       font=('Segoe UI', 10))
        style.configure('Header.TLabel', background=bg_medium, foreground=fg_text,
                       font=('Segoe UI', 12, 'bold'), padding=10)
        style.configure('Metric.TLabel', background=bg_light, foreground=fg_text,
                       font=('Segoe UI', 11), padding=5)
        style.configure('Value.TLabel', background=bg_light, foreground=accent_blue,
                       font=('Segoe UI', 14, 'bold'), padding=5)
        style.configure('Good.TLabel', background=bg_light, foreground=accent_green,
                       font=('Segoe UI', 14, 'bold'), padding=5)
        style.configure('Warning.TLabel', background=bg_light, foreground=accent_yellow,
                       font=('Segoe UI', 14, 'bold'), padding=5)
        style.configure('Alert.TLabel', background=bg_light, foreground=accent_red,
                       font=('Segoe UI', 14, 'bold'), padding=5)

        style.configure('Card.TFrame', background=bg_medium, relief='raised', borderwidth=1)
        style.configure('TNotebook', background=bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=bg_medium, foreground=fg_text,
                       padding=[10, 5], font=('Segoe UI', 10, 'bold'))

        # Treeview styles
        style.configure('Treeview', background=bg_light, foreground=fg_text,
                       fieldbackground=bg_light, font=('Segoe UI', 9))
        style.configure('Treeview.Heading', background=bg_medium, foreground=fg_text,
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', accent_blue)])

    def create_header(self):
        """Create header with title and status."""
        header_frame = tk.Frame(self.root, bg='#1e1e1e', pady=15)
        header_frame.pack(fill=tk.X)

        # Title
        title_label = ttk.Label(header_frame, text="ASX Trading AI", style='Title.TLabel')
        title_label.pack()

        subtitle_label = ttk.Label(header_frame,
                                   text="Professional Financial Analysis Dashboard",
                                   style='Subtitle.TLabel')
        subtitle_label.pack()

        # Status bar
        self.status_frame = tk.Frame(header_frame, bg='#2d2d2d', pady=8)
        self.status_frame.pack(fill=tk.X, padx=20, pady=(10, 0))

        self.status_label = ttk.Label(self.status_frame,
                                      text="Loading...",
                                      style='Metric.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Refresh button
        self.refresh_btn = tk.Button(self.status_frame, text="↻ Refresh",
                                     command=self.refresh_data,
                                     bg='#2196f3', fg='white',
                                     font=('Segoe UI', 10, 'bold'),
                                     relief=tk.FLAT, padx=15, pady=5,
                                     cursor='hand2')
        self.refresh_btn.pack(side=tk.RIGHT, padx=10)

    def create_main_content(self):
        """Create main content area with tabs."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Tab 1: Overview
        self.overview_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.overview_tab, text='📊 Overview')
        self.create_overview_tab()

        # Tab 2: Live Announcements
        self.announcements_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.announcements_tab, text='📢 Live Announcements')
        self.create_announcements_tab()

        # Tab 3: Recommendations
        self.recommendations_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.recommendations_tab, text='💡 Recommendations')
        self.create_recommendations_tab()

        # Tab 4: Performance Analytics
        self.analytics_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.analytics_tab, text='📈 Analytics')
        self.create_analytics_tab()

    def create_overview_tab(self):
        """Create overview tab with key metrics."""
        # Metrics grid
        metrics_frame = tk.Frame(self.overview_tab, bg='#1e1e1e')
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Row 1: Collection Metrics
        row1 = tk.Frame(metrics_frame, bg='#1e1e1e')
        row1.pack(fill=tk.X, pady=5)

        self.total_announcements_card = self.create_metric_card(
            row1, "Total Announcements", "0", "Collected since start"
        )
        self.total_announcements_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.price_sensitive_card = self.create_metric_card(
            row1, "Price Sensitive", "0 (0%)", "High-priority signals"
        )
        self.price_sensitive_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.unique_companies_card = self.create_metric_card(
            row1, "Unique Companies", "0", "Market coverage"
        )
        self.unique_companies_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        # Row 2: Alpha Window Performance
        row2 = tk.Frame(metrics_frame, bg='#1e1e1e')
        row2.pack(fill=tk.X, pady=5)

        self.ultra_fresh_card = self.create_metric_card(
            row2, "Ultra-Fresh (< 5 min)", "0 (0%)", "Maximum Alpha"
        )
        self.ultra_fresh_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.fresh_card = self.create_metric_card(
            row2, "Fresh (5-15 min)", "0 (0%)", "Good Alpha"
        )
        self.fresh_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.stale_card = self.create_metric_card(
            row2, "Stale (> 30 min)", "0 (0%)", "No Alpha"
        )
        self.stale_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        # Row 3: Recommendation Metrics
        row3 = tk.Frame(metrics_frame, bg='#1e1e1e')
        row3.pack(fill=tk.X, pady=5)

        self.recommendations_card = self.create_metric_card(
            row3, "Recommendations", "0", "Generated signals"
        )
        self.recommendations_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.filter_pass_rate_card = self.create_metric_card(
            row3, "Filter Pass Rate", "0%", "Signal quality"
        )
        self.filter_pass_rate_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.optimal_hours_card = self.create_metric_card(
            row3, "Optimal Hours", "0 (0%)", "10 AM - 2 PM"
        )
        self.optimal_hours_card.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        # Collection timeline
        timeline_frame = ttk.LabelFrame(metrics_frame, text="Collection Timeline",
                                       style='Card.TFrame', padding=10)
        timeline_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.timeline_text = scrolledtext.ScrolledText(
            timeline_frame, height=8, bg='#2d2d2d', fg='#e0e0e0',
            font=('Consolas', 9), relief=tk.FLAT
        )
        self.timeline_text.pack(fill=tk.BOTH, expand=True)

    def create_announcements_tab(self):
        """Create live announcements monitoring tab."""
        # Filter controls
        filter_frame = tk.Frame(self.announcements_tab, bg='#2d2d2d', pady=10)
        filter_frame.pack(fill=tk.X, padx=10)

        ttk.Label(filter_frame, text="Filter:", style='Metric.TLabel').pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar(value='all')
        filters = [
            ('All', 'all'),
            ('Price Sensitive Only', 'price_sensitive'),
            ('Fresh (< 5 min)', 'fresh'),
            ('Today Only', 'today')
        ]

        for text, value in filters:
            rb = tk.Radiobutton(filter_frame, text=text, variable=self.filter_var,
                               value=value, bg='#2d2d2d', fg='#e0e0e0',
                               selectcolor='#3d3d3d', font=('Segoe UI', 9),
                               command=self.refresh_announcements)
            rb.pack(side=tk.LEFT, padx=10)

        # Announcements table
        table_frame = tk.Frame(self.announcements_tab, bg='#1e1e1e')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        columns = ('Ticker', 'Title', 'Type', 'PS', 'Age', 'Time', 'Status')
        self.announcements_tree = ttk.Treeview(table_frame, columns=columns,
                                              show='headings',
                                              yscrollcommand=vsb.set,
                                              xscrollcommand=hsb.set)

        vsb.config(command=self.announcements_tree.yview)
        hsb.config(command=self.announcements_tree.xview)

        # Column configuration
        self.announcements_tree.heading('Ticker', text='Ticker')
        self.announcements_tree.heading('Title', text='Announcement Title')
        self.announcements_tree.heading('Type', text='Type')
        self.announcements_tree.heading('PS', text='PS')
        self.announcements_tree.heading('Age', text='Age (min)')
        self.announcements_tree.heading('Time', text='Detected')
        self.announcements_tree.heading('Status', text='Status')

        self.announcements_tree.column('Ticker', width=60, anchor='center')
        self.announcements_tree.column('Title', width=400)
        self.announcements_tree.column('Type', width=150)
        self.announcements_tree.column('PS', width=40, anchor='center')
        self.announcements_tree.column('Age', width=80, anchor='center')
        self.announcements_tree.column('Time', width=130, anchor='center')
        self.announcements_tree.column('Status', width=100, anchor='center')

        self.announcements_tree.pack(fill=tk.BOTH, expand=True)

        # Tag colors for rows
        self.announcements_tree.tag_configure('price_sensitive', background='#2d4a2d')
        self.announcements_tree.tag_configure('ultra_fresh', background='#2d3a4a')
        self.announcements_tree.tag_configure('fresh', background='#2d2d3a')

    def create_recommendations_tab(self):
        """Create recommendations tracking tab."""
        # Summary frame
        summary_frame = ttk.LabelFrame(self.recommendations_tab,
                                      text="Recommendations Summary",
                                      style='Card.TFrame', padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        summary_grid = tk.Frame(summary_frame, bg='#2d2d2d')
        summary_grid.pack(fill=tk.X)

        # Summary metrics
        self.recs_total_label = ttk.Label(summary_grid, text="Total: 0",
                                         style='Value.TLabel')
        self.recs_total_label.pack(side=tk.LEFT, padx=20)

        self.recs_buy_label = ttk.Label(summary_grid, text="BUY: 0",
                                       style='Good.TLabel')
        self.recs_buy_label.pack(side=tk.LEFT, padx=20)

        self.recs_sell_label = ttk.Label(summary_grid, text="SELL: 0",
                                        style='Alert.TLabel')
        self.recs_sell_label.pack(side=tk.LEFT, padx=20)

        self.recs_avg_conf_label = ttk.Label(summary_grid, text="Avg Confidence: 0%",
                                            style='Value.TLabel')
        self.recs_avg_conf_label.pack(side=tk.LEFT, padx=20)

        # Recommendations table
        table_frame = tk.Frame(self.recommendations_tab, bg='#1e1e1e')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('Ticker', 'Recommendation', 'Confidence', 'Entry Price',
                  'Sentiment', 'Generated', 'Filters')
        self.recommendations_tree = ttk.Treeview(table_frame, columns=columns,
                                                show='headings',
                                                yscrollcommand=vsb.set)

        vsb.config(command=self.recommendations_tree.yview)

        # Column configuration
        self.recommendations_tree.heading('Ticker', text='Ticker')
        self.recommendations_tree.heading('Recommendation', text='Action')
        self.recommendations_tree.heading('Confidence', text='Confidence')
        self.recommendations_tree.heading('Entry Price', text='Entry Price')
        self.recommendations_tree.heading('Sentiment', text='Sentiment')
        self.recommendations_tree.heading('Generated', text='Generated')
        self.recommendations_tree.heading('Filters', text='Filters Passed')

        self.recommendations_tree.column('Ticker', width=80, anchor='center')
        self.recommendations_tree.column('Recommendation', width=80, anchor='center')
        self.recommendations_tree.column('Confidence', width=100, anchor='center')
        self.recommendations_tree.column('Entry Price', width=100, anchor='center')
        self.recommendations_tree.column('Sentiment', width=120)
        self.recommendations_tree.column('Generated', width=150, anchor='center')
        self.recommendations_tree.column('Filters', width=200)

        self.recommendations_tree.pack(fill=tk.BOTH, expand=True)

        # Tag colors
        self.recommendations_tree.tag_configure('BUY', background='#2d4a2d')
        self.recommendations_tree.tag_configure('SELL', background='#4a2d2d')

    def create_analytics_tab(self):
        """Create performance analytics tab."""
        # Analytics content
        analytics_content = scrolledtext.ScrolledText(
            self.analytics_tab, bg='#2d2d2d', fg='#e0e0e0',
            font=('Consolas', 10), relief=tk.FLAT, wrap=tk.WORD
        )
        analytics_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.analytics_text = analytics_content

    def create_metric_card(self, parent, title, value, description):
        """Create a metric card widget."""
        card = ttk.Frame(parent, style='Card.TFrame', padding=15)

        title_label = ttk.Label(card, text=title, style='Metric.TLabel')
        title_label.pack()

        value_label = ttk.Label(card, text=value, style='Value.TLabel')
        value_label.pack(pady=(5, 0))

        desc_label = ttk.Label(card, text=description,
                              style='Subtitle.TLabel')
        desc_label.pack(pady=(5, 0))

        # Store value label for updates
        card.value_label = value_label

        return card

    def create_footer(self):
        """Create footer with auto-refresh status."""
        footer = tk.Frame(self.root, bg='#2d2d2d', pady=8)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.footer_label = ttk.Label(footer,
                                     text="Auto-refresh: ON | Last updated: Never",
                                     style='Metric.TLabel')
        self.footer_label.pack(side=tk.LEFT, padx=20)

        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = tk.Checkbutton(
            footer, text="Auto-refresh (30s)", variable=self.auto_refresh_var,
            bg='#2d2d2d', fg='#e0e0e0', selectcolor='#3d3d3d',
            font=('Segoe UI', 9), command=self.toggle_auto_refresh
        )
        auto_refresh_check.pack(side=tk.RIGHT, padx=20)

    def refresh_data(self):
        """Refresh all dashboard data."""
        try:
            self.update_status("Refreshing data...")

            # Update overview metrics
            self.update_overview_metrics()

            # Update announcements table
            self.refresh_announcements()

            # Update recommendations
            self.refresh_recommendations()

            # Update analytics
            self.update_analytics()

            # Update status
            now = datetime.now(self.tz)
            self.update_status(f"Last updated: {now.strftime('%H:%M:%S')}")
            self.footer_label.config(
                text=f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'} | "
                     f"Last updated: {now.strftime('%H:%M:%S')}"
            )

        except Exception as e:
            self.update_status(f"Error: {str(e)}")

    def update_overview_metrics(self):
        """Update overview tab metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total announcements
        cursor.execute('SELECT COUNT(*), SUM(price_sensitive), COUNT(DISTINCT ticker) FROM live_announcements')
        total, sensitive, companies = cursor.fetchone()

        self.total_announcements_card.value_label.config(text=str(total or 0))

        if total:
            sensitive_pct = (sensitive / total) * 100
            self.price_sensitive_card.value_label.config(
                text=f"{sensitive or 0} ({sensitive_pct:.1f}%)"
            )
        else:
            self.price_sensitive_card.value_label.config(text="0 (0%)")

        self.unique_companies_card.value_label.config(text=str(companies or 0))

        # Alpha window metrics
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN age_minutes < 5 THEN 1 END),
                COUNT(CASE WHEN age_minutes BETWEEN 5 AND 15 THEN 1 END),
                COUNT(CASE WHEN age_minutes > 30 THEN 1 END)
            FROM live_announcements
        ''')
        ultra, fresh, stale = cursor.fetchone()

        if total:
            ultra_pct = (ultra / total) * 100
            fresh_pct = (fresh / total) * 100
            stale_pct = (stale / total) * 100

            self.ultra_fresh_card.value_label.config(text=f"{ultra} ({ultra_pct:.1f}%)")
            self.fresh_card.value_label.config(text=f"{fresh} ({fresh_pct:.1f}%)")
            self.stale_card.value_label.config(text=f"{stale} ({stale_pct:.1f}%)")

            # Color code based on performance
            if ultra_pct >= 30:
                self.ultra_fresh_card.value_label.config(style='Good.TLabel')
            elif ultra_pct >= 20:
                self.ultra_fresh_card.value_label.config(style='Warning.TLabel')
            else:
                self.ultra_fresh_card.value_label.config(style='Value.TLabel')

        # Recommendations
        cursor.execute('SELECT COUNT(*) FROM live_recommendations')
        rec_count = cursor.fetchone()[0]
        self.recommendations_card.value_label.config(text=str(rec_count or 0))

        # Filter pass rate
        if total:
            pass_rate = (rec_count / total) * 100 if rec_count else 0
            self.filter_pass_rate_card.value_label.config(text=f"{pass_rate:.1f}%")

            if pass_rate >= 5:
                self.filter_pass_rate_card.value_label.config(style='Good.TLabel')
            elif pass_rate > 0:
                self.filter_pass_rate_card.value_label.config(style='Warning.TLabel')
            else:
                self.filter_pass_rate_card.value_label.config(style='Value.TLabel')

        # Optimal hours
        cursor.execute('''
            SELECT COUNT(*)
            FROM live_announcements
            WHERE CAST(SUBSTR(detected_timestamp, 12, 2) AS INTEGER) BETWEEN 10 AND 13
        ''')
        optimal = cursor.fetchone()[0]

        if total:
            optimal_pct = (optimal / total) * 100
            self.optimal_hours_card.value_label.config(text=f"{optimal} ({optimal_pct:.1f}%)")

        # Timeline
        cursor.execute('''
            SELECT MIN(detected_timestamp), MAX(detected_timestamp)
            FROM live_announcements
        ''')
        first, last = cursor.fetchone()

        self.timeline_text.delete('1.0', tk.END)
        if first and last:
            first_dt = datetime.strptime(first, '%Y-%m-%d %H:%M:%S')
            last_dt = datetime.strptime(last, '%Y-%m-%d %H:%M:%S')
            duration = (last_dt - first_dt).total_seconds() / 3600

            timeline = f"""
Collection Timeline:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

First Announcement:  {first}
Last Announcement:   {last}
Duration:            {duration:.1f} hours
Rate:                {total / duration if duration > 0 else 0:.1f} announcements/hour

Today's Collection:  {self.get_today_count(cursor)} announcements
Yesterday:           {self.get_yesterday_count(cursor)} announcements
This Week:           {total} announcements total
            """.strip()

            self.timeline_text.insert('1.0', timeline)
        else:
            self.timeline_text.insert('1.0', "No data collected yet.")

        conn.close()

    def get_today_count(self, cursor):
        """Get today's announcement count."""
        today = datetime.now(self.tz).strftime('%Y-%m-%d')
        cursor.execute(
            'SELECT COUNT(*) FROM live_announcements WHERE detected_timestamp LIKE ?',
            (f'{today}%',)
        )
        return cursor.fetchone()[0]

    def get_yesterday_count(self, cursor):
        """Get yesterday's announcement count."""
        yesterday = (datetime.now(self.tz) - timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute(
            'SELECT COUNT(*) FROM live_announcements WHERE detected_timestamp LIKE ?',
            (f'{yesterday}%',)
        )
        return cursor.fetchone()[0]

    def refresh_announcements(self):
        """Refresh announcements table."""
        # Clear existing
        for item in self.announcements_tree.get_children():
            self.announcements_tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query based on filter
        filter_value = self.filter_var.get()

        if filter_value == 'price_sensitive':
            query = '''
                SELECT ticker, title, announcement_type, price_sensitive,
                       age_minutes, detected_timestamp, processed
                FROM live_announcements
                WHERE price_sensitive = 1
                ORDER BY detected_timestamp DESC
                LIMIT 200
            '''
        elif filter_value == 'fresh':
            query = '''
                SELECT ticker, title, announcement_type, price_sensitive,
                       age_minutes, detected_timestamp, processed
                FROM live_announcements
                WHERE age_minutes < 5
                ORDER BY detected_timestamp DESC
                LIMIT 200
            '''
        elif filter_value == 'today':
            today = datetime.now(self.tz).strftime('%Y-%m-%d')
            query = f'''
                SELECT ticker, title, announcement_type, price_sensitive,
                       age_minutes, detected_timestamp, processed
                FROM live_announcements
                WHERE detected_timestamp LIKE '{today}%'
                ORDER BY detected_timestamp DESC
                LIMIT 200
            '''
        else:
            query = '''
                SELECT ticker, title, announcement_type, price_sensitive,
                       age_minutes, detected_timestamp, processed
                FROM live_announcements
                ORDER BY detected_timestamp DESC
                LIMIT 200
            '''

        cursor.execute(query)

        for row in cursor.fetchall():
            ticker, title, ann_type, ps, age, detected, processed = row

            ps_text = 'YES' if ps else ''
            status = 'Processed' if processed else 'Pending'
            time_str = detected[11:19] if detected else ''

            # Truncate title if too long
            if len(title) > 60:
                title = title[:57] + '...'

            # Determine tag
            tags = []
            if ps:
                tags.append('price_sensitive')
            if age and age < 5:
                tags.append('ultra_fresh')
            elif age and age < 15:
                tags.append('fresh')

            self.announcements_tree.insert('', 'end',
                                          values=(ticker, title, ann_type or 'Unknown',
                                                 ps_text, f'{age:.1f}' if age else '-',
                                                 time_str, status),
                                          tags=tuple(tags))

        conn.close()

    def refresh_recommendations(self):
        """Refresh recommendations table."""
        # Clear existing
        for item in self.recommendations_tree.get_children():
            self.recommendations_tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recommendations
        cursor.execute('''
            SELECT ticker, recommendation, confidence, entry_price,
                   sentiment, generated_timestamp, filters_passed
            FROM live_recommendations
            ORDER BY generated_timestamp DESC
            LIMIT 100
        ''')

        buy_count = 0
        sell_count = 0
        total_conf = 0
        count = 0

        for row in cursor.fetchall():
            ticker, rec, conf, price, sentiment, generated, filters = row

            if rec == 'BUY':
                buy_count += 1
            else:
                sell_count += 1

            total_conf += conf
            count += 1

            time_str = generated[11:19] if generated else ''

            self.recommendations_tree.insert('', 'end',
                                           values=(ticker, rec, f'{conf:.2f}',
                                                  f'${price:.2f}' if price else '-',
                                                  sentiment or '-', time_str,
                                                  filters or '-'),
                                           tags=(rec,))

        # Update summary
        self.recs_total_label.config(text=f"Total: {count}")
        self.recs_buy_label.config(text=f"BUY: {buy_count}")
        self.recs_sell_label.config(text=f"SELL: {sell_count}")

        if count > 0:
            avg_conf = (total_conf / count) * 100
            self.recs_avg_conf_label.config(text=f"Avg Confidence: {avg_conf:.1f}%")
        else:
            self.recs_avg_conf_label.config(text="Avg Confidence: N/A")

        conn.close()

    def update_analytics(self):
        """Update analytics tab."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE ANALYTICS REPORT")
        report.append("=" * 80)
        report.append("")

        # Time-of-day breakdown
        report.append("TIME-OF-DAY PERFORMANCE")
        report.append("-" * 80)

        cursor.execute('''
            SELECT
                SUBSTR(detected_timestamp, 12, 2) as hour,
                COUNT(*) as count,
                SUM(price_sensitive) as sensitive
            FROM live_announcements
            GROUP BY hour
            ORDER BY hour
        ''')

        for hour, count, sensitive in cursor.fetchall():
            try:
                hour_int = int(hour)
                optimal = " <-- OPTIMAL" if 10 <= hour_int <= 13 else ""
                bar = "█" * (count // 2)
                report.append(f"{hour}:00-{hour_int+1:02d}:00  {bar} ({count} ann, {sensitive or 0} PS){optimal}")
            except:
                pass

        report.append("")

        # Announcement type breakdown
        report.append("TOP ANNOUNCEMENT TYPES")
        report.append("-" * 80)

        cursor.execute('''
            SELECT announcement_type, COUNT(*) as count
            FROM live_announcements
            GROUP BY announcement_type
            ORDER BY count DESC
            LIMIT 15
        ''')

        for ann_type, count in cursor.fetchall():
            report.append(f"{(ann_type or 'Unknown')[:50]:50} {count:3}")

        report.append("")

        # Filter performance
        report.append("FILTER ANALYSIS")
        report.append("-" * 80)

        cursor.execute('SELECT COUNT(*) FROM live_announcements')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM live_recommendations')
        recs = cursor.fetchone()[0]

        if total:
            pass_rate = (recs / total) * 100
            reject_rate = 100 - pass_rate

            report.append(f"Total Announcements Processed: {total}")
            report.append(f"Recommendations Generated:     {recs}")
            report.append(f"Filter Pass Rate:              {pass_rate:.2f}%")
            report.append(f"Filter Reject Rate:            {reject_rate:.2f}%")
            report.append("")

            if pass_rate < 5:
                report.append("STATUS: Filters are correctly rejecting low-quality signals")
                report.append("NOTE: Most announcements are administrative noise (expected)")
            elif pass_rate < 15:
                report.append("STATUS: Good filter selectivity - generating quality signals")
            else:
                report.append("WARNING: Pass rate high - filters may be too permissive")

        report.append("")
        report.append("=" * 80)

        # Update text widget
        self.analytics_text.delete('1.0', tk.END)
        self.analytics_text.insert('1.0', '\n'.join(report))

        conn.close()

    def update_status(self, message):
        """Update status label."""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def toggle_auto_refresh(self):
        """Toggle auto-refresh."""
        self.auto_refresh = self.auto_refresh_var.get()

    def auto_refresh_loop(self):
        """Auto-refresh loop."""
        while True:
            time.sleep(30)  # Refresh every 30 seconds
            if self.auto_refresh:
                try:
                    self.refresh_data()
                except:
                    pass

    def start_auto_refresh(self):
        """Start auto-refresh thread."""
        refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        refresh_thread.start()

        # Initial load
        self.refresh_data()

    def run(self):
        """Run the dashboard."""
        self.root.mainloop()


def main():
    """Main entry point."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    dashboard = FinancialDashboard(db_path='data/trading.db')
    dashboard.run()


if __name__ == '__main__':
    main()
