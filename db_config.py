# Supabase PostgreSQL Configuration
# Project: Transfer and Posting
# 
# HOW IT WORKS - HYBRID SYNC MODE:
# ================================
# 1. Data is ALWAYS stored locally in SQLite for fast access
# 2. When online, changes are automatically synced to Supabase
# 3. When offline, you can still work - changes sync when reconnected
# 4. Click "Sync Now" button to manually sync at any time
# 5. Auto-sync runs every 2 minutes when online
#
# INSTRUCTIONS:
# 1. Replace 'YOUR_PASSWORD_HERE' with your Supabase database password
# 2. You can find the password in Supabase Dashboard > Settings > Database
# 3. Set USE_ONLINE_DATABASE = True to enable online sync
# 4. Set USE_ONLINE_DATABASE = False to work completely offline
#
# NOTE: Using Session Pooler for better IPv4/IPv6 compatibility

DB_CONFIG = {
    'host': 'aws-1-ap-south-1.pooler.supabase.com',
    'port': 6543,  # Transaction pooler port (use this if 5432 is blocked by ISP)
    # 'port': 5432,  # Standard PostgreSQL port (blocked by some office networks)
    'database': 'postgres',
    'user': 'postgres.qkhpacqsztvpnkrfmwgz',
    'password': 'Revathyr@j6123',  # Replace with your Supabase database password
}

# Set to True to enable online sync with PostgreSQL, False to work completely offline
USE_ONLINE_DATABASE = True

# Connection string format (alternative - Session Pooler)
# postgresql://postgres.qkhpacqsztvpnkrfmwgz:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
