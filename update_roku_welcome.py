#!/usr/bin/env python3
"""
Script to update Roku welcome screen with guest information from reservations.csv.
Automatically extracts first names from guest names, processes only confirmed/active 
reservations, and includes transition day logic for checkout/check-in overlaps.
When no guests are currently hosting, displays a generic "Welcome Guest," message.
Usage: python3 update_roku_welcome.py
"""

import sys
import json
import requests
import csv
import datetime
import time
import os
from io import StringIO

# ============================================================================
# CONFIGURATION - Update these values when your session expires
# See CONFIGURATION.md for detailed instructions on getting new session tokens
# ============================================================================

# Roku session token (main authentication - expires after hours/days)
# GET THIS FROM: Roku account settings -> Guest Mode -> Developer Tools -> Network Tab
ROKU_SESSION_TOKEN = 'YOUR_ROKU_SESSION_TOKEN_HERE'

# Device ID (should not change unless you switch Roku devices)
# GET THIS FROM: Same network request as above - look for device ID in URL
ROKU_DEVICE_ID = "YOUR_ROKU_DEVICE_ID_HERE"

# Airbnb API credentials (unique per listing - should not change often)
# GET THIS FROM: Airbnb host dashboard -> Network Tab when loading reservations
AIRBNB_API_KEY = 'YOUR_AIRBNB_API_KEY_HERE'

# ============================================================================


# JSON API function removed - now using CSV API directly as primary method


def download_airbnb_reservations():
    """
    Download the latest reservations CSV data directly from Airbnb.
    Automatically saves successful downloads to reservations.csv and detects changes.
    
    Returns:
        str: CSV data as string, or None if download fails
    """
    print("📥 Downloading from Airbnb...")
    
    # Airbnb API endpoint with parameters
    url = "https://www.airbnb.com/api/v2/download_reservations"
    
    # Current date for the date_min parameter
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # COMPREHENSIVE PARAMETERS - Updated from latest working curl command (2025-01-31)
    params = {
        '_format': 'for_remy',
        '_limit': '40',
        '_offset': '0',
        'collection_strategy': 'for_reservations_list',
        'date_min': current_date,
        'sort_field': 'start_date',
        'sort_order': 'asc',
        'status': 'accepted,request',
        'page': '1',
        'key': AIRBNB_API_KEY,
        'currency': 'USD',
        'locale': 'en'
    }
    
    # COMPREHENSIVE COOKIES - Updated from latest working curl command (2025-01-31)
    cookies = {
        # Core authentication cookies (required)
        '_aat': '0%7ClmaG85F9njvxHnk420cEGma6OH6TM%2BbmGor%2FPfuJfaxvk3E%2BGucQQVitUiZl6d6W',
        '_airbed_session_id': '967b1422c8f43e2a0b585ae3ff86fb91',
        '_csrf_token': 'V4%24.airbnb.com%24ycLJQ7depGY%24NJNulRdO7QcmSvSlUjDVCKj8j8qc8hI2hd11WPf3DC4%3D',
        
        # Session tracking cookies
        'auth_jitney_session_id': '90edf323-d98d-4c5a-948a-a6a3aa70df98',
        'jitney_client_session_id': 'da668238-d81a-4edf-baaf-b0f4bc010484',
        'jitney_client_session_created_at': '1759295169.053',
        'jitney_client_session_updated_at': '1759296320.417',
        
        # User context and preferences
        '_user_attributes': '%7B%22curr%22%3A%22USD%22%2C%22id%22%3A24395468%2C%22id_str%22%3A%2224395468%22%2C%22is_admin%22%3Afalse%7D',
        'country': 'US',
        'sticky_locale': 'en',
        'tzo': '-420',
        'hli': '1',
        'li': '1',
        
        # Security and verification cookies
        '_scid': '65c096f6-931c-495e-bf32-9097f04667cc',
        '_iidt': 'LpO6yXgRVGKHob0xp8HS3J14oF4ieT0OBCcrPxoePUgtNaqnR8q37PG4v9L+uWTnWy/KZBlceiSWs+89sqIGtNnntlTQKXa3lqf7hjo=',
        '_vid_t': 'RHdvjYn68/UF9IU1S6OO+XaoUcnKnZEQpm6sCzTkFqaHdzvwdK3ac9j8Kn0oWl2GnO7/kYokYvLKTFw1rkydeoY9EhFlH72w5pATY/E=',
        '_aaj': '27%7C2%7CxU0jMEfFNjHFMk5%2FEcssx%2BJZJ5x%2BMCsTW4xGyeEt2l%2BlwHRRGliPx%2BTmpUOOYeI18PgauO3bsrcTk7XLe6C7dTmLG0biLyNWsHnHWTgZ8AtOURdkOt6b2PckfRAPUX1Mf3PM1sqsBBexCIxfKPViXQSS8FY%2FYouXl%2Bh%2FWqaCVMUSOdE%2FJ6Cr07Ws6Kt%2FRUnuFK6yLi4TEocOZzO2YtYxRPUK0NBDJ6vxwAk7QXNDXS8TZNMd4Y9H3OM%2BWjGO09OQ3eZyJIH0k2ygRk3XvqGQcLX%2BTsxM9RbXQSE85paUvGMuLFwshwTH1P4pxBZJDtAX1N1lUgdCL8t32J2yRG02FAaThbOy2JnpBDDBgT7%2FALNwdTM2PjRPCMxaMh7JvktMl8yeLyjnFXyoFsoWOvKB7LZ3Tt6c6uU9p06ZzFuiIT%2BIvOPpKQRbQ8NwtfNumy0WWUOreU0hP5moMxZlF0gwq6miqjiCTjmnDljN4m9NYlDvTaGJvybhk65Tz8e4UpQeKO1Y3%2FpPJlpS5EQZhty0INgMYMIvsxOkMrCM0uXw%2FDBQpeZGY9DpWT%2FrvGpJoQi5nK7PfOM%2FsHyYKgnmt1As6JLOF1QuWI6AOYx39r1AYE5pxCCuciQl9siKFXIRYIKFRKeZkrWxTiUQ7I5UNWBhkPxBk28m3a7TLymTEUySIKHIBsMbCdRpumXxboii6uLREL43tTB85ev%2BmL3amxbFKVfwPPPGh%2B1A2P6%2FISV1EarBFwuSlIdvBcn3MpU479selpennhnidiIlKVlPFnNgigXizSLhCc3wgNBIacnRbAWvnXyBDW1tuvHQanFeuBC3p48IxJidmhOTM7E%3D',
        
        # Experiment and feature flags
        'cdn_exp_5d4847f3128303184': 'treatment',
        'cdn_exp_d12d391c39114cc6a': 'treatment',
        'cdn_exp_12abc5c2c444da7a4': 'treatment',
        'cdn_exp_d652210e07870cfc3': 'control',
        
        # Bot management and tracking
        'ak_bmsc': 'A9E38A74A6C2B0D265E914FCC40A1FB5~000000000000000000000000000000~YAAQitAuFynQnJOZAQAAhOQpnh1ABnhbRQ+7cCLjfS3CAeQRDAojnekTDyAxbmnXT7hGXgVS7uOOI79dym4EoWEZtwDeL4n4skFL30Q9bN4v/hSjQrAec7EjINNl/4U9M8vtbPpvFFQM0ELieiJIW/T9jRHVymc4S5lTnzztQEQsHrnPK4NPjidGCCkQa0XLg87j4WMmrROTocDg0A6BvFMSIYJqfJmYPNvmUmDIgdcOwoy/s3NpUr1e7wWfjNw6CuMft0omtTa7X6FCLCMSKZDYAdKXD8ksFGDjJ4j7RiFrcfk/88vNSZVvBPWdRGRFL9fyYTz7eb3Yc4RVyE9Mleaj6pYZXs1FsjZbuD4XBarmxcPXFJWHcmd1pfLWdrm+p/ajgszeC0nAMFVe',
        'bm_sv': '91C9BC350CCFF9C3706CA8959471BE2C~YAAQjtAuF1pCQJeZAQAAwk08nh3ypTr4/JZpfeZOdFevJWo6L0MqvgjYDej8U/rJnnoQvM1UG1p7ZDjnK1uioweO/6R4IRltz7xjhj5uxe09XI4RV/qXCbqbdGcs4Lqqr5PIORvqXPayQ0bwLB/EGt26rMRhTPY192zPyzQvM2Ua7yMM0mVhPzZ/VfTG1Wc7MwhGvtkJFcK0MLvLCWo0tohhvmmVXekzUqLhxdKWDpSZ8JC+sVNQ3K28z3aOFqX216o=~1',
        
        # Additional tracking and preferences
        'everest_cookie': '1738974831.EANTViYjkwNmI1ZWFkMz.xle_WGlpJGpk5Fjqh4Sfvew3V-LfqBmo9fyj73E4_xU',
        'bev': '1704294757_MDBhYzFjYThjNzgz',
        '_ccv': 'cban%3A0_183215%3D1%2C0_200000%3D1%2C0_183345%3D1%2C0_183243%3D1%2C0_183216%3D1%2C0_179751%3D1%2C0_200003%3D1%2C0_200005%3D1%2C0_179754%3D1%2C0_179750%3D1%2C0_179737%3D1%2C0_179744%3D1%2C0_179739%3D1%2C0_179743%3D1%2C0_179749%3D1%2C0_200012%3D1%2C0_200011%3D1%2C0_183217%3D1%2C0_183219%3D1%2C0_183096%3D1%2C0_179747%3D1%2C0_179740%3D1%2C0_179752%3D1%2C0_183241%3D1%2C0_200007%3D1%2C0_183346%3D1%2C0_183095%3D1%2C0_210000%3D1%2C0_210001%3D1%2C0_210002%3D1%2C0_210003%3D1%2C0_210004%3D1%2C0_210010%3D1%2C0_210012%3D1%2C0_210008%3D1%2C0_210016%3D1%2C0_210017%3D1',
        '_gtmeec': 'eyJlbSI6ImUyODVlMGY4ODAxNTQyNGQ0YjdjNTk3MzBkNzc4MWZlZjFkMTU0ZjViMjc2MDZmYmViYzA3M2VkYjczYTQ3OWQiLCJwaCI6ImQ2YmI2Y2Y3N2QxNjdiOWE4OGE5NmZmODBiMzRjNDRjZGRlNjkxNjFjYmNmMGIxZjNmNGVmNjkwZTRhOTdjOGUiLCJsbiI6ImE4MjFjNjJlODEwNGY4NTE5ZDYzOWI0YzA5NDhhZWNlNjQxYjE0M2Y2NjAxZmExNDU5OTNiYjJlMmM3Mjk5ZDQiLCJmbiI6IjA0ZjgxZjM3YjA0MTg2NjY0ODYwNmQ3OGMwMjNkMGFjMDE2YTgwZGQ5YmIzZjQzN2JlYWQ4ODNkYTY0NDczZGEiLCJjdCI6ImUzYjBjNDQyOThmYzFjMTQ5YWZiZjRjODk5NmZiOTI0MjdhZTQxZTQ2NDliOTM0Y2E0OTU5OTFiNzg1MmI4NTUiLCJzdCI6ImUzYjBjNDQyOThmYzFjMTQ5YWZiZjRjODk5NmZiOTI0MjdhZTQxZTQ2NDliOTM0Y2E0OTU5OTFiNzg1MmI4NTUiLCJnZSI6IjYyYzY2YTdhNWRkNzBjMzE0NjYxODA2M2MzNDRlNTMxZTZkNGI1OWUzNzk4MDg0NDNjZTk2MmIzYWJkNjNjNWEiLCJkYiI6IjMwYTg2ZjRkODIzOWFhYWFmOTMxYzVmOTYxY2YxNjdjM2UxYmVmNmViNmVhYzEyYWUwN2Y2YTVjYjkzZDlhNzIiLCJjb3VudHJ5IjoiZTNiMGM0NDI5OGZjMWMxNDlhZmJmNGM4OTk2ZmI5MjQyN2FlNDFlNDY0OWI5MzRjYTQ5NTk5MWI3ODUyYjg1NSIsImV4dGVybmFsX2lkIjoiMTcwNDI5NDc1N19NREJoWXpGallUaGpOemd6In0%3D',
        '_pt': '1--WyI5NmE4NmEwODhkYjlmMmJjNzFmM2UwN2MwMmFkY2Y5MzExMDI3Y2M4Il0%3D--cefaeef64b9bc3bb99fb697f3ed02b1d0402a51f',
        'muxData': 'mux_viewer_id=9156477d-0c17-4013-be6c-c37af3182f8a&msn=0.3984703195230075&sid=c8f206fd-36a7-4173-8022-7722eb6a6a8b&sst=1758782244817&sex=1758783822100',
        '_cci': 'cban%3Aac-36acb479-8ce5-4c3c-a929-39824e1f6ccb',
        'rclu': '3%7C2%7CEFqR4KAG04dr2YpjZrDDQ4smnQHCf5clIKLXdIFDv9YPopDV5ftToirIltbgQvNSqBXoK2mkuE%2FjZmUZvspElHDYrrWBNrVJJhy6N2nKFjIonldfeWO7hnNCdAJwkqpKQ0m%2FiIzehcfkqBiLM1sk52qC1inXbj0fjwJoymbVVA%3D%3D',
        'previousTab': '%7B%22id%22%3A%223930c807-6c1b-4aa8-9471-2757425a658a%22%7D',
        'frmfctr': 'wide',
        'cfrmfctr': 'DESKTOP',
        'cbkp': '3'
    }
    
    # COMPREHENSIVE HEADERS - Updated from latest working curl command (2025-01-31)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,zh;q=0.6',
        'ect': '4g',
        'priority': 'u=0, i',
        'referer': 'https://www.airbnb.com/hosting/reservations',
        'sec-ch-device-memory': '8',
        'sec-ch-dpr': '2',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-ch-ua-platform-version': '"15.6.1"',
        'sec-ch-viewport-width': '1185',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(
            url=url,
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            new_data = response.text
            print(f"✅ Downloaded ({len(new_data)} chars)")
            
            # Check for changes and update local file
            _update_local_reservations_file(new_data)
            
            return new_data
        else:
            print(f"❌ Download failed: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Download error: {e}")
        return None


# JSON to CSV conversion function removed - now using direct CSV API


def _update_local_reservations_file(new_data):
    """
    Compare new CSV data with existing local file and update if changes detected.
    
    Args:
        new_data (str): New CSV data from Airbnb
    """
    local_file = "reservations.csv"
    
    # Read existing file if it exists
    existing_data = None
    if os.path.exists(local_file):
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                existing_data = f.read()
        except IOError as e:
            print(f"⚠️  Warning: Could not read existing {local_file}: {e}")
    
    # Compare data to detect changes
    if existing_data is None:
        # No existing file
        print(f"📄 Creating new {local_file}")
        changes_detected = True
    elif existing_data.strip() == new_data.strip():
        # No changes detected
        print(f"✨ No changes detected in reservations")
        changes_detected = False
    else:
        # Changes detected
        print(f"🔄 Changes detected in reservations")
        changes_detected = True
    
    # Update local file if changes detected
    if changes_detected:
        try:
            with open(local_file, 'w', encoding='utf-8') as f:
                f.write(new_data)
            print(f"💾 Updated {local_file}")
        except IOError as e:
            print(f"❌ Error: Could not write to {local_file}: {e}")
    else:
        print(f"📁 Local {local_file} is up to date")


def update_roku_welcome(first_name):
    """
    Send a PUT request to update the Roku welcome screen title.
    
    Args:
        first_name (str): The first name to include in the welcome message
    
    Returns:
        bool: True if successful, False otherwise
    """
    # API endpoint using configured device ID
    url = f"https://my.roku.com/account/api/v1/guest-mode/host-settings/{ROKU_DEVICE_ID}"
    
    
    # Cookies - only ks.session is needed for authentication
    cookies = {
        'ks.session': ROKU_SESSION_TOKEN,
    }
    
    # Create the welcome message with the provided first name (respecting Roku constraints)
    welcome_message = create_welcome_message(first_name)
    
    print(f"Message: '{welcome_message}' ({len(welcome_message)} chars)")
    
    # Request payload
    data = {
        "welcomeScreenTitle": welcome_message
    }
    
    try:
        print("Updating Roku...")
        
        # Send the PUT request
        response = requests.put(
            url=url,
            cookies=cookies,
            json=data,
            timeout=30
        )
        
        
        # Check if the request was successful (simplified validation)
        if response.status_code == 200:
            print("✅ Roku updated")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False


def extract_first_name(full_name):
    """
    Extract the first name from a full guest name.
    
    Args:
        full_name (str): Full guest name
        
    Returns:
        str: First name only
    """
    if not full_name:
        return ""
    
    # Split by space and take the first part
    parts = full_name.strip().split()
    if parts:
        return parts[0]
    return full_name.strip()


def create_welcome_message(first_name):
    """
    Create a welcome message within Roku constraints (40 chars max).
    Format: "{firstName}, Welcome to Seattle!"
    
    Args:
        first_name (str): Guest's first name
        
    Returns:
        str: Formatted single-line welcome message
    """
    # Single line format
    message = f"{first_name}, Welcome to Seattle!"
    
    # Check if the message fits within the 40-character limit
    if len(message) <= 40:
        return message
    
    # If too long, try shorter format
    short_message = f"{first_name}, Welcome!"
    if len(short_message) <= 40:
        return short_message
    
    # If name is still too long, truncate it
    max_name_length = 40 - len(", Welcome!")  # Leave room for ", Welcome!"
    if len(first_name) > max_name_length:
        truncated_name = first_name[:max_name_length]
        return f"{truncated_name}, Welcome!"
    
    # Final fallback
    return "Welcome!"


def parse_reservation_date(date_string):
    """
    Parse reservation date from CSV (MM/DD/YYYY format).
    
    Args:
        date_string (str): Date string from CSV
        
    Returns:
        datetime.date: Parsed date object or None if parsing fails
    """
    if not date_string:
        return None
        
    try:
        # Parse MM/DD/YYYY format
        return datetime.datetime.strptime(date_string.strip(), '%m/%d/%Y').date()
    except ValueError:
        try:
            # Try YYYY-MM-DD format as backup
            return datetime.datetime.strptime(date_string.strip(), '%Y-%m-%d').date()
        except ValueError:
            print(f"⚠️  Date parse error: '{date_string}'")
            return None


def is_currently_hosting(start_date_str, end_date_str, current_date):
    """
    Check if a guest is currently hosting based on start/end dates.
    
    Args:
        start_date_str (str): Start date from CSV
        end_date_str (str): End date from CSV  
        current_date (datetime.date): Current date to compare against
        
    Returns:
        bool: True if guest is currently hosting, False otherwise
    """
    start_date = parse_reservation_date(start_date_str)
    end_date = parse_reservation_date(end_date_str)
    
    if start_date is None or end_date is None:
        return False
    
    # Guest is currently hosting if current date is between start date (inclusive) and end date (exclusive)
    # End date is checkout day, so guest is no longer hosting on that date
    return start_date <= current_date < end_date


def read_csv_schedule(csv_file_path=None, csv_data=None):
    """
    Read reservations CSV file or data and return confirmed entries that should be processed.
    
    Args:
        csv_file_path (str, optional): Path to the reservations CSV file
        csv_data (str, optional): CSV data as string
        
    Returns:
        list: List of dictionaries containing schedule entries
    """
    if csv_data:
        # Use provided CSV data string
        csvfile = StringIO(csv_data)
        reader = csv.DictReader(csvfile)
    elif csv_file_path and os.path.exists(csv_file_path):
        # Use local CSV file
        csvfile = open(csv_file_path, 'r', newline='', encoding='utf-8')
        reader = csv.DictReader(csvfile)
    else:
        print(f"❌ Error: No valid CSV data or file found")
        return []
    
    entries = []
    try:
        # Check if required columns exist
        if 'Start date' not in reader.fieldnames or 'Guest name' not in reader.fieldnames:
            print("❌ Missing CSV columns: 'Start date' or 'Guest name'")
            print(f"📋 Found: {reader.fieldnames}")
            return []
        
        for row in reader:
            status = row.get('Status', '').strip()
            start_date = row.get('Start date', '').strip()
            guest_name = row.get('Guest name', '').strip()
            
            # Process all reservations with valid date and guest data (ignore status)
            if start_date and guest_name:
                first_name = extract_first_name(guest_name)
                end_date = row.get('End date', '').strip()
                if first_name:  # Make sure we extracted a valid first name
                    entries.append({
                        'start_date': start_date,
                        'end_date': end_date,
                        'first_name': first_name,
                        'full_name': guest_name,
                        'status': status,
                        'confirmation_code': row.get('Confirmation code', '').strip()
                    })
                    
    except Exception as e:
        print(f"❌ Error reading CSV data: {e}")
        return []
    finally:
        # Close file if we opened one
        if csv_file_path and hasattr(csvfile, 'close'):
            csvfile.close()
    
    print(f"Loaded {len(entries)} reservations")
    return entries



def update_welcome_from_reservations(csv_file_path=None, use_airbnb_api=True):
    """
    Download latest reservations and update Roku welcome message.
    
    Args:
        csv_file_path (str, optional): Path to local CSV file as fallback
        use_airbnb_api (bool): Whether to try downloading from Airbnb first
    """
    print(f"Starting update...")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    entries = []
    
    # Try downloading from Airbnb CSV API directly
    if use_airbnb_api:
        csv_data = download_airbnb_reservations()
        if csv_data:
            entries = read_csv_schedule(csv_data=csv_data)
        else:
            print("⚠️ API download failed, using local file...")
    
    # Fallback to local CSV file if download failed or not requested
    if not entries and csv_file_path:
        print(f"📂 Using local: {csv_file_path}")
        entries = read_csv_schedule(csv_file_path=csv_file_path)
    
    if len(entries) == 0:
        print("❌ No confirmed reservations found")
        return False
    
    # Determine who is currently hosting based on dates and checkout/check-in transition logic
    current_datetime = datetime.datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    checkin_cutoff_time = datetime.time(11, 0)  # 11:00 AM
    
    currently_hosting = []
    checking_out_today = []
    checking_in_today = []
    confirmed = []
    
    for entry in entries:
        start_date = parse_reservation_date(entry['start_date'])
        end_date = parse_reservation_date(entry['end_date'])
        
        if start_date is None or end_date is None:
            confirmed.append(entry)
            continue
            
        # Check for transition day scenarios (checkout/check-in on same day)
        if end_date == current_date:
            checking_out_today.append(entry)
        if start_date == current_date:
            checking_in_today.append(entry)
            
        # Check if guest is currently hosting (normal date range logic)
        if is_currently_hosting(entry['start_date'], entry['end_date'], current_date):
            currently_hosting.append(entry)
        else:
            confirmed.append(entry)
    
    # Special logic for checkout/check-in transition days
    transition_day_logic = False
    if checking_out_today and checking_in_today:
        transition_day_logic = True
        if current_time < checkin_cutoff_time:
            # Before 11 AM: prioritize checkout guest
            first_entry = checking_out_today[0]
            priority_reason = f"Checkout day before 11 AM (ends: {first_entry['end_date']})"
        else:
            # After 11 AM: prioritize check-in guest
            first_entry = checking_in_today[0]
            priority_reason = f"Check-in day after 11 AM (starts: {first_entry['start_date']})"
    elif currently_hosting:
        first_entry = currently_hosting[0]
        priority_reason = f"Currently hosting (dates: {first_entry['start_date']} to {first_entry['end_date']})"
    elif confirmed:
        first_entry = confirmed[0]
        priority_reason = "Future or past reservation"
    else:
        first_entry = entries[0]
        priority_reason = "First available reservation"
    
    # Determine first name to use
    if len(currently_hosting) == 0 and not transition_day_logic:
        first_name = "Guest"
        guest_display_name = "Property vacant"
        priority_reason = "No active guests - using generic welcome"
    else:
        first_name = first_entry['first_name']
        guest_display_name = first_entry['full_name']
    
    print(f"Found {len(entries)} reservations, {len(currently_hosting)} active")
    
    if transition_day_logic:
        checkout_names = [e['full_name'] for e in checking_out_today]
        checkin_names = [e['full_name'] for e in checking_in_today]
        status = "checkout" if current_time < checkin_cutoff_time else "checkin"
        print(f"🔄 Transition day: {checkout_names[0]} (ends) → {checkin_names[0]} (starts)")
        print(f"⏰ Current time: {current_time.strftime('%H:%M')} | Cutoff: 11:00 | Priority: {status}")
    elif currently_hosting:
        names = [e['full_name'] for e in currently_hosting[:2]]
        print(f"Active: {', '.join(names)}")
    
    print(f"Selected: {guest_display_name} → {first_name}")
    
    # Update the Roku welcome screen
    success = update_roku_welcome(first_name)
    
    if success:
        print(f"✅ Complete: \"{create_welcome_message(first_name)}\"")
        return True
    else:
        print(f"❌ Update failed for {first_name}")
        return False


def main():
    """Main function to execute the welcome message update."""
    # Local CSV filename as fallback
    csv_file_path = "reservations.csv"
    
    # Update welcome message (tries Airbnb API first, then local file)
    success = update_welcome_from_reservations(csv_file_path=csv_file_path, use_airbnb_api=True)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
