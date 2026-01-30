"""
Utility functions for the Flask application.
"""
from datetime import datetime


def convert_date_format(date_str):
    """
    Convert date from various formats to desktop app format (DD-MM-YYYY).
    
    Handles multiple input formats:
    - YYYY-MM-DD (HTML date input)
    - DD/MM/YYYY
    - DD-MM-YYYY (already in target format)
    - MM/DD/YYYY (American format)
    - MM-DD-YYYY (American format)
    - MM DD YYYY (American format with spaces)
    - YYYY/MM/DD
    - DD.MM.YYYY
    - Text month formats like "Jan 15 2024", "15 Jan 2024", etc.
    
    Args:
        date_str: Date string in various formats or empty string
        
    Returns:
        Date string in DD-MM-YYYY format or empty string if conversion fails
    """
    if not date_str or not str(date_str).strip():
        return ''
    
    date_str = str(date_str).strip()
    
    # If already in DD-MM-YYYY format (day 01-31, month 01-12), return as is
    if len(date_str) == 10 and date_str[2] == '-' and date_str[5] == '-':
        try:
            # Validate it's actually DD-MM-YYYY not MM-DD-YYYY
            day = int(date_str[:2])
            month = int(date_str[3:5])
            if 1 <= day <= 31 and 1 <= month <= 12:
                return date_str
        except ValueError:
            pass
    
    # List of formats to try - ORDER MATTERS!
    # First try unambiguous formats, then ambiguous ones
    formats_to_try = [
        # Unambiguous formats (year first or text month)
        '%Y-%m-%d',      # YYYY-MM-DD (HTML date input format) - MOST COMMON
        '%Y/%m/%d',      # YYYY/MM/DD
        '%Y.%m.%d',      # YYYY.MM.DD
        '%d %b %Y',      # 15 Jan 2024
        '%d-%b-%Y',      # 15-Jan-2024
        '%d/%b/%Y',      # 15/Jan/2024
        '%b %d %Y',      # Jan 15 2024
        '%b %d, %Y',     # Jan 15, 2024
        '%d %B %Y',      # 15 January 2024
        '%B %d %Y',      # January 15 2024
        '%B %d, %Y',     # January 15, 2024
        
        # DD/MM/YYYY formats (European - day first) - TRY FIRST for ambiguous
        '%d/%m/%Y',      # DD/MM/YYYY (European)
        '%d-%m-%Y',      # DD-MM-YYYY (European)
        '%d.%m.%Y',      # DD.MM.YYYY (European)
        '%d %m %Y',      # DD MM YYYY (European with spaces)
        
        # MM/DD/YYYY formats (American - month first)
        '%m/%d/%Y',      # MM/DD/YYYY (American)
        '%m-%d-%Y',      # MM-DD-YYYY (American)
        '%m %d %Y',      # MM DD YYYY (American with spaces)
    ]
    
    for fmt in formats_to_try:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime('%d-%m-%Y')
        except ValueError:
            continue
    
    # Special handling for ambiguous dates like "01/02/2024"
    # Try to detect if it's MM/DD/YYYY (month > 12 in first position is impossible)
    # or DD/MM/YYYY
    for separator in ['/', '-', ' ', '.']:
        parts = date_str.split(separator)
        if len(parts) == 3:
            try:
                first = int(parts[0])
                second = int(parts[1])
                third = int(parts[2])
                
                # Determine year position
                if third > 31:  # Year is last (most common)
                    year = third
                    # If first > 12, it must be day (European format)
                    if first > 12:
                        day, month = first, second
                    # If second > 12, it must be day (American format)
                    elif second > 12:
                        month, day = first, second
                    else:
                        # Ambiguous - assume European DD/MM/YYYY as it's more common in India
                        day, month = first, second
                elif first > 31:  # Year is first
                    year = first
                    month, day = second, third
                else:
                    continue
                
                # Validate
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    return f'{day:02d}-{month:02d}-{year}'
            except (ValueError, IndexError):
                continue
    
    # If nothing worked, return original string
    return date_str

