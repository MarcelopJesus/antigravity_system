
import gspread
import os
import time
import datetime

# Monkeypatch time to be 1 year in the past (2024)
# Current env time is 2025-12-30. We want 2024-12-30.
# 1 year = 365 * 24 * 3600 = 31536000 seconds.
# But 2024 might be a leap year (yes it is). So 366 days?
# Let's just create a custom time function.

real_time = time.time
def mocked_time():
    # If the system thinks it is 2025, reduce by ~1 year (31536000 seconds)
    # Just to be safe, let's subtract 366 days = 31622400 seconds
    return real_time() - 31622400

# Apply patch
time.time = mocked_time

import google.auth
# google.auth uses time.time() or datetime.datetime.utcnow() to set 'iat' and 'exp'
# Patching time.time should cover jwt generation in google-auth

def debug_gspread_patched():
    path = 'config/service_account.json'
    print(f"Testing gspread with TIME PATCH (back to 2024)...")
    print(f"Original Time: {datetime.datetime.fromtimestamp(real_time())}")
    print(f"Patched Time: {datetime.datetime.fromtimestamp(time.time())}")
    
    ssid = "1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4" 
    
    try:
        gc = gspread.service_account(filename=path)
        print("gspread Client created.")
        
        print(f"Attempting to open spreadsheet {ssid}...")
        sh = gc.open_by_key(ssid)
        print(f"Success! Spreadsheet Title: {sh.title}")
        
    except Exception as e:
        print(f"gspread Error with patch: {e}")

if __name__ == "__main__":
    debug_gspread_patched()
