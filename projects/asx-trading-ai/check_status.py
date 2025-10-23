"""
Quick status check for live trading system.
Run anytime to see current progress.
"""
import sqlite3
from datetime import datetime
import pytz

DB_PATH = 'data/trading.db'
TZ = pytz.timezone('Australia/Sydney')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

now = datetime.now(TZ)

print("="*80)
print(f"LIVE TRADING SYSTEM STATUS - {now.strftime('%Y-%m-%d %H:%M:%S AEST')}")
print("="*80)
print()

# Announcements
cursor.execute('SELECT COUNT(*) FROM live_announcements')
total_announcements = cursor.fetchone()[0]

cursor.execute('''
    SELECT COUNT(*) FROM live_announcements
    WHERE detected_timestamp > datetime('now', '-1 hour')
''')
recent_announcements = cursor.fetchone()[0]

print(f"ANNOUNCEMENTS:")
print(f"  Total collected: {total_announcements}")
print(f"  Last hour: {recent_announcements}")
print()

# Recommendations
cursor.execute('SELECT COUNT(*) FROM live_recommendations')
total_recs = cursor.fetchone()[0]

cursor.execute('''
    SELECT COUNT(*) FROM live_recommendations
    WHERE generated_timestamp > datetime('now', '-1 hour')
''')
recent_recs = cursor.fetchone()[0]

if total_announcements > 0:
    pass_rate = (total_recs / total_announcements) * 100
else:
    pass_rate = 0

print(f"RECOMMENDATIONS:")
print(f"  Total generated: {total_recs}")
print(f"  Last hour: {recent_recs}")
print(f"  Pass rate: {pass_rate:.1f}%")
print()

# Trades
cursor.execute('SELECT COUNT(*) FROM trade_outcomes WHERE status = "OPEN"')
open_trades = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM trade_outcomes WHERE status = "CLOSED"')
closed_trades = cursor.fetchone()[0]

cursor.execute('''
    SELECT
        SUM(return_dollars) as total_pnl,
        AVG(return_pct) as avg_return,
        MIN(return_pct) as worst,
        MAX(return_pct) as best
    FROM trade_outcomes
    WHERE status = "OPEN"
''')
total_pnl, avg_return, worst, best = cursor.fetchone()
total_pnl = total_pnl or 0
avg_return = avg_return or 0
worst = worst or 0
best = best or 0

print(f"TRADES:")
print(f"  Open: {open_trades}")
print(f"  Closed: {closed_trades}")
print(f"  Total P&L: ${total_pnl:+.2f}")
print(f"  Avg return: {avg_return:+.2f}%")
print(f"  Range: {worst:.2f}% to {best:+.2f}%")
print()

# Closed trades breakdown
cursor.execute('''
    SELECT outcome, COUNT(*)
    FROM trade_outcomes
    WHERE status = "CLOSED"
    GROUP BY outcome
''')
closed_breakdown = cursor.fetchall()

if closed_breakdown:
    print(f"CLOSED TRADES:")
    for outcome, count in closed_breakdown:
        print(f"  {outcome}: {count}")
    print()

# Recent activity
cursor.execute('''
    SELECT ticker, entry_price, return_pct, status, last_updated
    FROM trade_outcomes
    ORDER BY last_updated DESC
    LIMIT 5
''')
recent_trades = cursor.fetchall()

print(f"RECENT TRADES:")
for ticker, entry, ret, status, updated in recent_trades:
    ret = ret or 0
    print(f"  {ticker:6} @ ${entry:7.2f} | {ret:+6.2f}% [{status:6}] - {updated}")

print()
print("="*80)
print("Dashboard: http://localhost:8000")
print("Log file: data/live_system.log")
print("="*80)

conn.close()
