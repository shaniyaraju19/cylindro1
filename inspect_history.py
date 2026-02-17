import requests
import json
from datetime import datetime, timedelta

url = "http://esskay-012024.live/gasleve/get_gas_history.php"
try:
    res = requests.get(url, timeout=10)
    data = res.json()
    print("Type of data:", type(data))
    if isinstance(data, list):
        print("First item:", data[0] if data else "Empty list")
    elif isinstance(data, dict):
        print("Keys:", data.keys())
        print("Data dump:", json.dumps(data, indent=2)[:500])
    
    # Test logic
    if isinstance(data, list):
        print("\n--- Testing Logic ---")
        for i, r in enumerate(data):
            recent_time = datetime.now() - timedelta(minutes=i*30)
            print(f"Index {i}: Original {r.get('timestamp')} -> New {recent_time.strftime('%d-%m-%Y %I:%M %p')}")
            if i > 2: break

except Exception as e:
    print(f"Error: {e}")
