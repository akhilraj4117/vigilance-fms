"""
Utility functions for the Flask application.
"""
from datetime import datetime


def convert_date_format(date_str):
    """
    Convert date from HTML5 input format (YYYY-MM-DD) to desktop app format (DD-MM-YYYY).
    
    Args:
        date_str: Date string in YYYY-MM-DD format or empty string
        
    Returns:
        Date string in DD-MM-YYYY format or empty string if conversion fails
    """
    if not date_str or not date_str.strip():
        return ''
    
    date_str = date_str.strip()
    
    # If already in DD-MM-YYYY format, return as is
    if len(date_str) == 10 and date_str[2] == '-' and date_str[5] == '-':
        return date_str
    
    # Convert from YYYY-MM-DD to DD-MM-YYYY
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d-%m-%Y')
    except (ValueError, AttributeError):
        # If conversion fails, return the original string
        return date_str
