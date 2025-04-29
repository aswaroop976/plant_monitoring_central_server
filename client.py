import requests
import time

# Configuration
SERVER_URL = 'http://127.0.0.1:5000'  # Example: 'http://127.0.0.1:5000'

def fetch_moisture():
    try:
        response = requests.get(f'{SERVER_URL}/api/moisture')
        response.raise_for_status()  # Raise an error if not 2xx
        data = response.json()
        print(f"Moisture: {data.get('moisture', '--')}")
    except Exception as e:
        print(f"Error fetching moisture: {e}")

if __name__ == '__main__':
    while True:
        fetch_moisture()
        time.sleep(1)  # Fetch every 10 seconds
