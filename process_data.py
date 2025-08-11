# export_loans.py

import requests
import csv
from datetime import datetime
import pandas as pd
import re

headers = {
        "Authorization": "Token 58ffed2a92962674bdc906707bc9af2823d0120d"
}



responseDict = {
    "processed_data": "https://brightcomloans.loca.lt/loans/api/admin/loans/",
    "loans": "https://brightcomloans.loca.lt/loans/api/admin/loan-list/",
    "clients": "https://brightcomloans.loca.lt/loans/api/admin/clients/",
    "ledger": "https://brightcomloans.loca.lt/loans/api/admin/ledger/"
}

def normalize_manager(s: str) -> str:
    if not isinstance(s, str) or not s:
        return ""
    raw = s.split("\\")[-1]                           # after last backslash
    raw = re.sub(r'[^\w.\-]+$', '', raw.strip())      # strip trailing punctuation (e.g., comma)
    parts = re.split(r'[._\s]+', raw)                 # split on dot/underscore/whitespace
    parts = [p for p in parts if p]                   # drop empties
    return " ".join(p.capitalize() for p in parts)

# Fetch data
for key, url in responseDict.items():
    try:
        
        response = requests.get(url, headers=headers) 
        
        response.raise_for_status()
        data = response.json()
        print(f"API Response Status: {response.status_code}")
        print(f"Data type: {type(data)}")
        if isinstance(data, list):
            print(f"Number of records: {len(data)}")
        else:
            print(f"Data structure: not list, type: {type(data)}")

        # File path and name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"{key}.csv" 

        df = pd.DataFrame(data)
        try:
           df.rename(columns={'Total Paid': 'Total_Paid', 'Total Charged': 'Total_Charged'}, inplace=True)
           df['Managed_By'] = df['Managed_By'].apply(normalize_manager)
        except KeyError as e:
            print(f"KeyError: {e} - This column may not exist in the data.")
        df.to_csv(file_path, index=False)

        print(f"Data exported successfully to {file_path}")
        print(f"Total records exported: {len(data)}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        exit(1)
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {response.text}")
        exit(1)







