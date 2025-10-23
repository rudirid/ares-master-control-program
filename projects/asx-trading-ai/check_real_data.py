"""Check what real data is in the database."""
import sqlite3

conn = sqlite3.connect('data/trading.db')
cursor = conn.cursor()

# Count records
cursor.execute('SELECT COUNT(*) FROM live_announcements')
total_announcements = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM live_recommendations')
total_recommendations = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM trade_outcomes')
total_outcomes = cursor.fetchone()[0]

print("="*60)
print("REAL DATABASE CONTENTS")
print("="*60)
print(f"Total announcements: {total_announcements}")
print(f"Total recommendations: {total_recommendations}")
print(f"Total trade outcomes: {total_outcomes}")
print()

# Show latest real announcements
print("Latest 10 REAL announcements:")
print("-"*60)
cursor.execute('''
    SELECT ticker, title, price_sensitive, age_minutes, detected_timestamp
    FROM live_announcements
    ORDER BY detected_timestamp DESC
    LIMIT 10
''')
for row in cursor.fetchall():
    ticker, title, ps, age, ts = row
    ps_marker = "[PS]" if ps else "    "
    print(f"{ps_marker} {ticker:6} {title[:45]:45} ({age:.1f}min)")

# Check for sample vs real data
cursor.execute('''
    SELECT COUNT(*)
    FROM live_announcements
    WHERE title LIKE '%Quarterly Production Report%'
       OR title LIKE '%Trading Update - FY25%'
       OR title LIKE '%Earnings Beat%'
''')
sample_count = cursor.fetchone()[0]

if sample_count > 0:
    print(f"\n⚠️  WARNING: {sample_count} sample/test announcements detected")
    print("These need to be removed for live data only")

conn.close()
print("="*60)
