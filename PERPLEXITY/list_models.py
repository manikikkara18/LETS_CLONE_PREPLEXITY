import requests

API_KEY = "AIzaSyDVCsVZGJFzoX8YbfOjwCGwET-IpD7V4Z4"
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

response = requests.get(url)
print(response.json())
