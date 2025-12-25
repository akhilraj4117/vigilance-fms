import sqlite3
import os

# Change to the correct directory
os.chdir('D:\\Python Programs\\Program')

conn = sqlite3.connect('vigilance_files.db')
cur = conn.cursor()

# Check for entries with file_number containing '5694'
cur.execute("SELECT id, file_number, employee_name, pen FROM disciplinary_action_details WHERE file_number LIKE '%5694%'")
rows = cur.fetchall()
print(f"Entries with '5694' in file_number: {len(rows)}")
for row in rows:
    print(row)

# Check for entries with file_number containing '2653'
cur.execute("SELECT id, file_number, employee_name, pen FROM disciplinary_action_details WHERE file_number LIKE '%2653%'")
rows = cur.fetchall()
print(f"\nEntries with '2653' in file_number: {len(rows)}")
for row in rows:
    print(row)

conn.close()
