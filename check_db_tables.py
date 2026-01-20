import psycopg2

conn = psycopg2.connect(
    host='aws-1-ap-south-1.pooler.supabase.com',
    port=6543,
    database='postgres',
    user='postgres.qkhpacqsztvpnkrfmwgz',
    password='Revathyr@j6123'
)
cur = conn.cursor()

prefix = 'regular_december_2025_'

# Final analysis: check if someone MORE senior than cascade recipients was available
print('=== FINAL ANALYSIS: Should cascade vacancies have gone to more senior employees? ===')
print()

# Cascade recipients:
# - PEN 421712 (456 days) got Alappuzha cascade
# - PEN 619468 (115 days) got Alappuzha cascade

# Were there more senior employees waiting for Alappuzha?
print('=== Employees MORE SENIOR than 456 days who wanted Alappuzha but did NOT get it ===')
cur.execute(f"""
    SELECT j.pen, j.name, j.duration_days, j.weightage, j.district,
           CASE WHEN d.pen IS NOT NULL THEN d.transfer_to_district ELSE 'NOT IN DRAFT' END as got_district
    FROM {prefix}transfer_applied t
    INNER JOIN {prefix}jphn j ON t.pen = j.pen
    LEFT JOIN {prefix}transfer_draft d ON t.pen = d.pen
    WHERE t.pref1 = 'Alappuzha'
    AND (t.locked IS NULL OR t.locked != 'Yes')
    AND j.duration_days > 456
    AND (d.pen IS NULL OR d.transfer_to_district != 'Alappuzha')
    ORDER BY j.duration_days DESC
""")
rows = cur.fetchall()
print(f'Found {len(rows)} employees more senior than 456 days who wanted Alappuzha but got something else or nothing:')
for r in rows:
    print(f'  PEN: {r[0]}, {r[1][:20]:20s}, {r[2]:5d} days, Wtg: {str(r[3]):4s}, From: {r[4]}, Got: {r[5]}')
print()

# So PEN 654226 (681 days) got Ernakulam instead of Alappuzha
# Let's see if Ernakulam was their Pref2 and Alappuzha was full when they were processed
print('=== Check when Alappuzha vacancies were filled (order matters) ===')
cur.execute(f"""
    SELECT d.pen, j.name, j.duration_days, j.weightage, d.remarks, d.added_date
    FROM {prefix}transfer_draft d
    INNER JOIN {prefix}jphn j ON d.pen = j.pen
    WHERE d.transfer_to_district = 'Alappuzha'
    ORDER BY 
        CASE WHEN d.remarks IS NULL THEN 0 ELSE 1 END,  -- Non-cascade first
        j.duration_days DESC
""")
rows = cur.fetchall()
print(f'Alappuzha fills (15 vacancies + cascades):')
for idx, r in enumerate(rows, 1):
    remark = r[4] if r[4] else 'Initial'
    print(f'{idx:2d}. PEN: {r[0]}, {r[1][:20]:20s}, {r[2]:5d} days, Wtg: {str(r[3]):4s}, Type: {remark}')

conn.close()
