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

# Check MOC data
cur.execute("SELECT moc_date, moc_issued, moc_issued_by FROM disciplinary_action_details WHERE moc_date IS NOT NULL AND moc_date != '' LIMIT 10")
print('Sample MOC dates:')
for r in cur.fetchall():
    print(f'  moc_date={r[0]}, moc_issued={r[1]}, moc_issued_by={r[2]}')

# Check SCN data
cur.execute("SELECT scn_issued_date, scn_issued_by FROM disciplinary_action_details WHERE scn_issued_date IS NOT NULL AND scn_issued_date != '' LIMIT 10")
print('\nSample SCN dates:')
for r in cur.fetchall():
    print(f'  scn_issued_date={r[0]}, scn_issued_by={r[1]}')

# Check WSD data
cur.execute("SELECT wsd_sent_to_dhs_date FROM disciplinary_action_details WHERE wsd_sent_to_dhs_date IS NOT NULL AND wsd_sent_to_dhs_date != '' LIMIT 10")
print('\nSample WSD dates:')
for r in cur.fetchall():
    print(f'  wsd_sent_to_dhs_date={r[0]}')

# Check SCN Reply data
cur.execute("SELECT scn_reply_sent_to_dhs_date FROM disciplinary_action_details WHERE scn_reply_sent_to_dhs_date IS NOT NULL AND scn_reply_sent_to_dhs_date != '' LIMIT 10")
print('\nSample SCN Reply dates:')
for r in cur.fetchall():
    print(f'  scn_reply_sent_to_dhs_date={r[0]}')

# Count all records
cur.execute("SELECT COUNT(*) FROM disciplinary_action_details")
print(f'\nTotal DA records: {cur.fetchone()[0]}')

# Count with MOC issued
cur.execute("SELECT COUNT(*) FROM disciplinary_action_details WHERE moc_issued = 'Issued'")
print(f'Records with MOC Issued: {cur.fetchone()[0]}')

# Check actual values of moc_issued_by
cur.execute("SELECT DISTINCT moc_issued_by FROM disciplinary_action_details WHERE moc_issued_by IS NOT NULL AND moc_issued_by != ''")
print('\nDistinct moc_issued_by values:')
for r in cur.fetchall():
    print(f'  {r[0]}')

conn.close()
