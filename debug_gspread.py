
import gspread
import os
import json

def debug_gspread():
    path = 'config/service_account.json'
    print(f"Testing gspread with {path}...")
    
    # Load invalid ID just to trigger auth, or use the real one
    # Real one from previous view_file: "1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4"
    ssid = "1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4" 
    
    try:
        gc = gspread.service_account(filename=path)
        print("gspread Client created.")
        
        print(f"Attempting to open spreadsheet {ssid}...")
        sh = gc.open_by_key(ssid)
        print("Spreadsheet opened object created.")
        
        # We need to make a read call to actually hit the API and trigger auth
        print("Reading title...")
        print(f"Title: {sh.title}")
        
    except Exception as e:
        print(f"gspread Error: {e}")

if __name__ == "__main__":
    debug_gspread()
