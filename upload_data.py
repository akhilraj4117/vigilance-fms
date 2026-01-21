import sqlite3
import psycopg2
from db_config import DB_CONFIG

# Connect to local SQLite
local_conn = sqlite3.connect('jphn_regular_December_2025.db')
local_cursor = local_conn.cursor()

# Check local records
local_cursor.execute('SELECT COUNT(*) FROM jphn')
local_count = local_cursor.fetchone()[0]
print(f'Local SQLite records in jphn: {local_count}')

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port'],
    database=DB_CONFIG['database'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password'],
    sslmode='require'
)
pg_cursor = pg_conn.cursor()

# Check remote records
pg_cursor.execute('SELECT COUNT(*) FROM regular_december_2025_jphn')
remote_count = pg_cursor.fetchone()[0]
print(f'PostgreSQL records in regular_december_2025_jphn: {remote_count}')

if local_count > remote_count:
    print(f'\nLocal has {local_count - remote_count} more records. Uploading...')
    
    # Get all local records
    local_cursor.execute('SELECT * FROM jphn')
    local_records = local_cursor.fetchall()
    col_names = [desc[0] for desc in local_cursor.description]
    
    print(f'Columns: {col_names}')
    
    # Upload to PostgreSQL
    upload_count = 0
    for record in local_records:
        try:
            # Build upsert query
            placeholders = ', '.join(['%s'] * len(col_names))
            update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in col_names if col != 'pen'])
            
            pg_cursor.execute(f'''
                INSERT INTO regular_december_2025_jphn ({', '.join(col_names)})
                VALUES ({placeholders})
                ON CONFLICT (pen) DO UPDATE SET {update_set}
            ''', record)
            upload_count += 1
        except Exception as e:
            print(f'Error uploading record: {e}')
    
    pg_conn.commit()
    print(f'Uploaded {upload_count} records')
    
    # Also upload transfer_applied if exists
    try:
        local_cursor.execute('SELECT * FROM transfer_applied')
        applied_records = local_cursor.fetchall()
        applied_cols = [desc[0] for desc in local_cursor.description]
        
        for record in applied_records:
            try:
                placeholders = ', '.join(['%s'] * len(applied_cols))
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in applied_cols if col != 'pen'])
                
                pg_cursor.execute(f'''
                    INSERT INTO regular_december_2025_transfer_applied ({', '.join(applied_cols)})
                    VALUES ({placeholders})
                    ON CONFLICT (pen) DO UPDATE SET {update_set}
                ''', record)
            except Exception as e:
                print(f'Error uploading transfer_applied: {e}')
        
        pg_conn.commit()
        print(f'Uploaded {len(applied_records)} transfer_applied records')
    except Exception as e:
        print(f'transfer_applied table: {e}')
    
    # Also upload vacancy if exists
    try:
        local_cursor.execute('SELECT * FROM vacancy')
        vacancy_records = local_cursor.fetchall()
        vacancy_cols = [desc[0] for desc in local_cursor.description]
        
        for record in vacancy_records:
            try:
                placeholders = ', '.join(['%s'] * len(vacancy_cols))
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in vacancy_cols if col != 'district'])
                
                pg_cursor.execute(f'''
                    INSERT INTO regular_december_2025_vacancy ({', '.join(vacancy_cols)})
                    VALUES ({placeholders})
                    ON CONFLICT (district) DO UPDATE SET {update_set}
                ''', record)
            except Exception as e:
                print(f'Error uploading vacancy: {e}')
        
        pg_conn.commit()
        print(f'Uploaded {len(vacancy_records)} vacancy records')
    except Exception as e:
        print(f'vacancy table: {e}')

    # Also upload transfer_draft if exists
    try:
        local_cursor.execute('SELECT * FROM transfer_draft')
        draft_records = local_cursor.fetchall()
        draft_cols = [desc[0] for desc in local_cursor.description]
        
        for record in draft_records:
            try:
                placeholders = ', '.join(['%s'] * len(draft_cols))
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in draft_cols if col != 'pen'])
                
                pg_cursor.execute(f'''
                    INSERT INTO regular_december_2025_transfer_draft ({', '.join(draft_cols)})
                    VALUES ({placeholders})
                    ON CONFLICT (pen) DO UPDATE SET {update_set}
                ''', record)
            except Exception as e:
                print(f'Error uploading transfer_draft: {e}')
        
        pg_conn.commit()
        print(f'Uploaded {len(draft_records)} transfer_draft records')
    except Exception as e:
        print(f'transfer_draft table: {e}')

else:
    print('PostgreSQL has all records or more')

local_conn.close()
pg_conn.close()
print('Done!')
