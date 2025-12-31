
import json
import os
import datetime
import google.auth
from google.oauth2 import service_account

def debug_creds():
    path = 'config/service_account.json'
    print(f"Checking {path}...")
    
    with open(path, 'r') as f:
        try:
            data = json.load(f)
            print("JSON loaded successfully.")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            return

    pk = data.get('private_key', '')
    print(f"Private Key length: {len(pk)}")
    print(f"Private Key start: {repr(pk[:50])}")
    print(f"Private Key end: {repr(pk[-50:])}")
    
    if '\\n' in pk and '\n' not in pk:
        print("WARNING: Key contains literal \\n strings but no actual newlines. It might be over-escaped.")
    
    print(f"System time: {datetime.datetime.now()}")

    try:
        creds = service_account.Credentials.from_service_account_info(data)
        print("Credentials object created safely.")
        
        # Force a refresh to sign a JWT
        import google.auth.transport.requests
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        print("Credentials refreshed successfully! (JWT Signed & Exchanged)")
        
    except Exception as e:
        print(f"Auth Error: {e}")

if __name__ == "__main__":
    debug_creds()
