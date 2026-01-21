"""Check vacancy tables in database"""
import psycopg2

conn = psycopg2.connect(
    host='aws-1-ap-south-1.pooler.supabase.com',
    database='postgres',
    user='postgres.qkhpacqsztvpnkrfmwgz',
    password='Revathyr@j6123',
    port=5432,
    sslmode='require'
)
cur = conn.cursor()

# List ALL tables
print("=== ALL tables in database ===")
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = cur.fetchall()
for t in tables:
    print(t[0])

conn.close()
