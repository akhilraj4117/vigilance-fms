import psycopg2
from db_config import DB_CONFIG

conn = psycopg2.connect(
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port'],
    database=DB_CONFIG['database'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password'],
    sslmode='require'
)
cursor = conn.cursor()

# List all tables
cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' ORDER BY table_name
""")
print('Tables in database:')
for row in cursor.fetchall():
    print(f'  {row[0]}')

# Check regular_december_2025_jphn table
try:
    cursor.execute('SELECT COUNT(*) FROM regular_december_2025_jphn')
    print(f'\nRecords in regular_december_2025_jphn: {cursor.fetchone()[0]}')
except Exception as e:
    print(f'\nError reading regular_december_2025_jphn: {e}')

# Check general_2025_jphn table  
try:
    cursor.execute('SELECT COUNT(*) FROM general_2025_jphn')
    print(f'Records in general_2025_jphn: {cursor.fetchone()[0]}')
except Exception as e:
    print(f'Error reading general_2025_jphn: {e}')

conn.close()
