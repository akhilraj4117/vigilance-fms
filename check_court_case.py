import psycopg2

conn = psycopg2.connect(
    host='aws-1-ap-southeast-2.pooler.supabase.com',
    port=6543,
    database='postgres',
    user='postgres.tmlenfumgrdtywxoytzj',
    password='Revathyr@j6123',
    sslmode='require'
)
cur = conn.cursor()

# Check court case records
cur.execute('SELECT COUNT(*) FROM court_case_details')
print(f'Court case records: {cur.fetchone()[0]}')

# Check disciplinary action records
cur.execute('SELECT COUNT(*) FROM disciplinary_action_details')
print(f'Disciplinary action records: {cur.fetchone()[0]}')

# Check files table for court case types
cur.execute("SELECT COUNT(*) FROM files WHERE file_type = 'Court Case' OR category = 'Court Case'")
print(f'Files with Court Case type/category: {cur.fetchone()[0]}')

# Check join with files
cur.execute('SELECT COUNT(*) FROM files f JOIN court_case_details cc ON f.file_number = cc.file_number')
print(f'Files joined with court cases: {cur.fetchone()[0]}')

# Check join with DA
cur.execute('''
SELECT COUNT(*) FROM disciplinary_action_details da 
JOIN court_case_details cc ON da.file_number = cc.file_number
''')
print(f'DA records with court cases (joined): {cur.fetchone()[0]}')

# Sample court cases
cur.execute('SELECT file_number, case_no, name_of_forum FROM court_case_details LIMIT 5')
rows = cur.fetchall()
print('\nSample court cases:')
for r in rows:
    print(f'  file_number={r[0]}, case_no={r[1]}, forum={r[2]}')

# Check what file exists in files table with that court case file number
cur.execute("SELECT file_number FROM files WHERE file_number = 'A6-5921/2021/DMO(H)T'")
row = cur.fetchone()
print(f'\nFile A6-5921/2021/DMO(H)T exists in files table: {row is not None}')

conn.close()
