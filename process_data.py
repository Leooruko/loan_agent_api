# export_loans.py

import requests
import csv
from datetime import datetime
import pandas as pd
# Endpoint and Token
url = "https://brightcomloans.loca.lt/loans/api/admin/loans/"
headers = {
        "Authorization": "Token 58ffed2a92962674bdc906707bc9af2823d0120d"
}

# Fetch data
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    print(f"API Response Status: {response.status_code}")
    print(f"Data type: {type(data)}")
    if isinstance(data, list):
        print(f"Number of records: {len(data)}")
    else:
        print(f"Data structure: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from API: {e}")
    exit(1)
except ValueError as e:
    print(f"Error parsing JSON response: {e}")
    print(f"Response content: {response.text}")
    exit(1)

# File path and name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = f"processed_data.csv" 

df = pd.DataFrame(data)
df.to_csv(file_path, index=False)

print(f"Data exported successfully to {file_path}")
print(f"Total records exported: {len(data)}")






