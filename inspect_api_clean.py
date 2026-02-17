import requests
import json
from datetime import datetime

url = "http://esskay-012024.live/gasleve/get_gas_data.php"
try:
    res = requests.get(url, timeout=10)
    data = res.json()
    print(json.dumps(data, indent=2))
    
    if data and "data" in data:
        ts = data["data"].get("timestamp")
        print(f"\nAPI Timestamp: {ts}")
        print(f"System Time: {datetime.now()}")
    else:
        print("No data found")

except Exception as e:
    print(str(e))
