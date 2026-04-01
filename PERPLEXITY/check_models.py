import requests
import json

API_KEY = "AIzaSyDVCsVZGJFzoX8YbfOjwCGwET-IpD7V4Z4"
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

try:
    response = requests.get(url)
    data = response.json()
    if 'error' in data:
        print(f"API Error: {data['error']['message']}")
    else:
        for model in data.get('models', []):
            print(model['name'])
except Exception as e:
    print(f"Error: {e}")
