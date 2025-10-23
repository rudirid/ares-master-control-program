"""Check recommendation generation results."""
import sqlite3

conn = sqlite3.connect('data/trading.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM live_recommendations')
recs = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM live_announcements WHERE processed = 1')
processed = cursor.fetchone()[0]

print("="*60)
print("RECOMMENDATION ENGINE RESULTS")
print("="*60)
print(f"Processed: {processed}/270 announcements")
print(f"Recommendations generated: {recs}")
print(f"Pass rate: {(recs/270*100):.1f}%")
print()

if recs > 0:
    print("Latest recommendations:")
    print("-"*60)
    cursor.execute('''
        SELECT ticker, recommendation, confidence, sentiment, generated_timestamp
        FROM live_recommendations
        ORDER BY id DESC
        LIMIT 15
    ''')
    for row in cursor.fetchall():
        ticker, rec, conf, sent, ts = row
        print(f"{ticker:6} {rec:4} (conf: {conf:.2f}, {sent:8}) @ {ts}")
else:
    print("NO RECOMMENDATIONS - Checking why...")
    cursor.execute('''
        SELECT
            SUM(CASE WHEN processed = 1 AND recommendation_generated = 0 THEN 1 ELSE 0 END) as filtered_count
        FROM live_announcements
    ''')
    filtered = cursor.fetchone()[0]
    print(f"  {filtered} announcements were filtered out")

conn.close()
print("="*60)
