import requests
from datetime import datetime

url = "http://esskay-012024.live/gasleve/get_gas_data.php"
try:
    res = requests.get(url, timeout=10)
    data = res.json()
    print("Full JSON Response:", data)
    
    if data and "data" in data:
        timestamp = data["data"].get("timestamp")
        print("Timestamp from API:", timestamp)
        
        system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("System Time:", system_time)
    else:
        print("No 'data' field in response.")

except Exception as e:
    print(f"Error: {e}")
