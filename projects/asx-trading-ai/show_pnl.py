"""Show current P&L status."""
import sqlite3

conn = sqlite3.connect('data/trading.db')
cursor = conn.cursor()

print("="*80)
print("CURRENT TRADE P&L STATUS")
print("="*80)

cursor.execute('''
    SELECT ticker, entry_price, current_price, return_pct, return_dollars, status
    FROM trade_outcomes
    WHERE id >= 11
    ORDER BY id
''')

total_pnl = 0
for row in cursor.fetchall():
    ticker, entry, current, ret_pct, ret_dollars, status = row
    ret_pct = ret_pct or 0
    ret_dollars = ret_dollars or 0
    current = current or entry
    total_pnl += ret_dollars

    color = '+' if ret_pct > 0 else ' '
    print(f"{ticker:6} Entry: ${entry:6.2f} Current: ${current:6.2f} | "
          f"Return: {color}{ret_pct:6.2f}% (${ret_dollars:+7.2f}) [{status}]")

print("="*80)
print(f"TOTAL P&L: ${total_pnl:+.2f}")
print("="*80)

conn.close()
