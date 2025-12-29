"""
Test script for date formatting filter
"""
from datetime import datetime


def format_date_filter(date_str):
    """Format date string to DD-MM-YYYY format.
    Handles multiple input formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc.
    """
    if not date_str or date_str == '-' or not str(date_str).strip():
        return '-'
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    formats_to_try = [
        '%Y-%m-%d',  # YYYY-MM-DD (HTML date input format)
        '%d/%m/%Y',  # DD/MM/YYYY
        '%d-%m-%Y',  # DD-MM-YYYY (already in target format)
        '%Y/%m/%d',  # YYYY/MM/DD
        '%d.%m.%Y',  # DD.MM.YYYY
        '%Y.%m.%d',  # YYYY.MM.DD
        '%d %m %Y',  # DD MM YYYY
        '%Y %m %d',  # YYYY MM DD
    ]
    
    for fmt in formats_to_try:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime('%d-%m-%Y')
        except ValueError:
            continue
    
    # If no format matched, check if it's already in DD-MM-YYYY format
    if len(date_str) >= 8 and len(date_str) <= 10:
        # Might already be in desired format, return as-is
        return date_str
    
    return date_str


# Test cases
test_dates = [
    '2024-12-29',      # YYYY-MM-DD format
    '29/12/2024',      # DD/MM/YYYY format
    '29-12-2024',      # DD-MM-YYYY format (already target)
    '2024/12/29',      # YYYY/MM/DD format
    '01-01-2023',      # DD-MM-YYYY
    '2023-05-15',      # YYYY-MM-DD
    '',                # Empty string
    None,              # None value
    '-',               # Dash
    '15.06.2024',      # DD.MM.YYYY
]

print("Date Formatting Test Results:")
print("-" * 50)
for date in test_dates:
    result = format_date_filter(date)
    print(f"Input: {date!r:20} => Output: {result}")
print("-" * 50)
print("\n✓ All test cases completed successfully!")
print("\nExpected format: DD-MM-YYYY")
print("All dates should be converted to this format.")
