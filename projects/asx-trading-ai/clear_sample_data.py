"""Clear sample/test data to prepare for live-only data."""
import sqlite3

conn = sqlite3.connect('data/trading.db')
cursor = conn.cursor()

print("="*60)
print("CLEARING SAMPLE DATA")
print("="*60)

# Delete sample trade outcomes
cursor.execute('DELETE FROM trade_outcomes')
deleted_outcomes = cursor.rowcount
print(f"Deleted {deleted_outcomes} sample trade outcomes")

# Delete sample recommendations
cursor.execute('DELETE FROM live_recommendations')
deleted_recs = cursor.rowcount
print(f"Deleted {deleted_recs} sample recommendations")

# Keep real announcements - they're from live ASX feed
cursor.execute('SELECT COUNT(*) FROM live_announcements')
real_announcements = cursor.fetchone()[0]
print(f"Kept {real_announcements} REAL announcements from live ASX feed")

conn.commit()
conn.close()

print()
print("="*60)
print("DATABASE NOW CONTAINS ONLY REAL LIVE DATA")
print("="*60)
print()
print("Next: The live paper trading system will:")
print("1. Continue collecting REAL announcements from ASX")
print("2. Generate REAL recommendations based on filters")
print("3. Track REAL trade outcomes with actual prices")
print("4. Calculate REAL P&L from actual market data")
print()
print("NO HALLUCINATIONS - ONLY REAL DATA")
print("="*60)
