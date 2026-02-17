import requests
import sys

def check_url(url, description):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"[PASS] {description} is accessible (200 OK)")
            return True
        else:
            print(f"[FAIL] {description} returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] {description} - Connection refused (Is the server running?)")
        return False

success = True
success &= check_url("http://localhost:5000/", "Index Page")
success &= check_url("http://localhost:5000/static/css/style.css", "CSS File")

if success:
    print("\n✅ Verification Successful: Application structure is correct.")
    sys.exit(0)
else:
    print("\n❌ Verification Failed: Application structure is incorrect.")
    sys.exit(1)
