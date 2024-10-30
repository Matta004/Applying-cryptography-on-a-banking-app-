import requests

BASE_URL = 'http://mattahome.tplinkdns.com:5000'  # Adjust if using localhost

# Test health check endpoint
def test_health_check():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=10)
        print("Health Check:", response.json())
    except requests.exceptions.RequestException as e:
        print("Health Check Failed:", e)

# Test account check endpoint
def test_check_account():
    url = f"{BASE_URL}/check_account"
    params = {
        "username": "testuser",
        "email": "testuser@example.com"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        print("Account Check:", response.json())
    except requests.exceptions.RequestException as e:
        print("Account Check Failed:", e)

if __name__ == "__main__":
    test_health_check()
    test_check_account()
