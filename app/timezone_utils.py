# -*- coding: utf-8 -*-
"""
Timezone utilities for Shanghai (China Standard Time)
"""
from datetime import datetime, date, timezone, timedelta
import pytz

# Shanghai timezone
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

def get_shanghai_now():
    """Get current datetime in Shanghai timezone"""
    return datetime.now(SHANGHAI_TZ)

def get_shanghai_today():
    """Get current date in Shanghai timezone"""
    return get_shanghai_now().date()

def utc_to_shanghai(utc_datetime):
    """Convert UTC datetime to Shanghai timezone"""
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    return utc_datetime.astimezone(SHANGHAI_TZ)

def shanghai_to_utc(shanghai_datetime):
    """Convert Shanghai datetime to UTC"""
    if shanghai_datetime.tzinfo is None:
        shanghai_datetime = SHANGHAI_TZ.localize(shanghai_datetime)
    return shanghai_datetime.astimezone(pytz.utc).replace(tzinfo=None)

def get_timezone_from_location(location):
    """
    Get timezone name from location string.
    Uses a mapping of common cities/countries to timezones.
    Returns timezone name or None if not found.
    """
    if not location:
        return None
    
    location_lower = location.lower().strip()
    
    # Comprehensive timezone mapping for common locations
    timezone_map = {
        # Asia
        'china': 'Asia/Shanghai',
        'beijing': 'Asia/Shanghai',
        'shanghai': 'Asia/Shanghai',
        'guangzhou': 'Asia/Shanghai',
        'shenzhen': 'Asia/Shanghai',
        'hong kong': 'Asia/Hong_Kong',
        'hongkong': 'Asia/Hong_Kong',
        'taiwan': 'Asia/Taipei',
        'taipei': 'Asia/Taipei',
        'japan': 'Asia/Tokyo',
        'tokyo': 'Asia/Tokyo',
        'osaka': 'Asia/Tokyo',
        'korea': 'Asia/Seoul',
        'seoul': 'Asia/Seoul',
        'south korea': 'Asia/Seoul',
        'singapore': 'Asia/Singapore',
        'thailand': 'Asia/Bangkok',
        'bangkok': 'Asia/Bangkok',
        'vietnam': 'Asia/Ho_Chi_Minh',
        'hanoi': 'Asia/Ho_Chi_Minh',
        'india': 'Asia/Kolkata',
        'mumbai': 'Asia/Kolkata',
        'delhi': 'Asia/Kolkata',
        'dubai': 'Asia/Dubai',
        'uae': 'Asia/Dubai',
        
        # Europe
        'uk': 'Europe/London',
        'united kingdom': 'Europe/London',
        'london': 'Europe/London',
        'england': 'Europe/London',
        'britain': 'Europe/London',
        'france': 'Europe/Paris',
        'paris': 'Europe/Paris',
        'germany': 'Europe/Berlin',
        'berlin': 'Europe/Berlin',
        'munich': 'Europe/Berlin',
        'spain': 'Europe/Madrid',
        'madrid': 'Europe/Madrid',
        'barcelona': 'Europe/Madrid',
        'italy': 'Europe/Rome',
        'rome': 'Europe/Rome',
        'milan': 'Europe/Rome',
        'netherlands': 'Europe/Amsterdam',
        'amsterdam': 'Europe/Amsterdam',
        'russia': 'Europe/Moscow',
        'moscow': 'Europe/Moscow',
        'portugal': 'Europe/Lisbon',
        'lisbon': 'Europe/Lisbon',
        
        # Americas
        'usa': 'America/New_York',
        'us': 'America/New_York',
        'united states': 'America/New_York',
        'new york': 'America/New_York',
        'nyc': 'America/New_York',
        'boston': 'America/New_York',
        'washington': 'America/New_York',
        'chicago': 'America/Chicago',
        'texas': 'America/Chicago',
        'houston': 'America/Chicago',
        'dallas': 'America/Chicago',
        'denver': 'America/Denver',
        'los angeles': 'America/Los_Angeles',
        'la': 'America/Los_Angeles',
        'san francisco': 'America/Los_Angeles',
        'seattle': 'America/Los_Angeles',
        'california': 'America/Los_Angeles',
        'canada': 'America/Toronto',
        'toronto': 'America/Toronto',
        'vancouver': 'America/Vancouver',
        'mexico': 'America/Mexico_City',
        'brazil': 'America/Sao_Paulo',
        'argentina': 'America/Argentina/Buenos_Aires',
        
        # Oceania
        'australia': 'Australia/Sydney',
        'sydney': 'Australia/Sydney',
        'melbourne': 'Australia/Melbourne',
        'brisbane': 'Australia/Brisbane',
        'perth': 'Australia/Perth',
        'new zealand': 'Pacific/Auckland',
        'auckland': 'Pacific/Auckland',
        
        # Middle East & Africa
        'egypt': 'Africa/Cairo',
        'cairo': 'Africa/Cairo',
        'south africa': 'Africa/Johannesburg',
        'nigeria': 'Africa/Lagos',
        'lagos': 'Africa/Lagos',
        'israel': 'Asia/Jerusalem',
        'saudi arabia': 'Asia/Riyadh',
        'turkey': 'Europe/Istanbul',
        'istanbul': 'Europe/Istanbul',
    }
    
    # Try exact match first
    if location_lower in timezone_map:
        return timezone_map[location_lower]
    
    # Try partial match
    for key, tz in timezone_map.items():
        if key in location_lower or location_lower in key:
            return timezone_map[key]
    
    return None

def get_user_local_time(location):
    """
    Get current local time for a user based on their location.
    Returns a dictionary with time info or None if timezone cannot be determined.
    """
    if not location:
        return None
    
    tz_name = get_timezone_from_location(location)
    if not tz_name:
        return None
    
    try:
        user_tz = pytz.timezone(tz_name)
        now_utc = datetime.now(pytz.utc)
        local_time = now_utc.astimezone(user_tz)
        
        return {
            'time': local_time.strftime('%H:%M'),  # 24-hour format
            'time_12h': local_time.strftime('%I:%M %p'),  # 12-hour format
            'date': local_time.strftime('%Y-%m-%d'),
            'timezone': tz_name,
            'timezone_abbr': local_time.strftime('%Z'),
            'offset': local_time.strftime('%z'),
            'hour': local_time.hour,
        }
    except Exception as e:
        print(f"Error getting local time for {location}: {e}")
        return None
