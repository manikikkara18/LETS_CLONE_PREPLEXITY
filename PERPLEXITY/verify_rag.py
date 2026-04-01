import requests

# 1. Upload File with correct mime type
files = {'file': ('secret.txt', open('secret.txt', 'rb'), 'text/plain')}
upload_response = requests.post('http://localhost:5000/api/upload', files=files)
upload_data = upload_response.json()
print("Upload Result:", upload_data)

if upload_data.get('status') == 'success':
    file_uri = upload_data.get('file_uri')
    file_mime = upload_data.get('mime_type')
    
    # 2. Chat with File (passing mime_type)
    payload = {
        "message": "What is the password mentioned in this file?",
        "file_uri": file_uri,
        "file_mime": file_mime
    }
    chat_response = requests.post('http://localhost:5000/api/chat', json=payload)
    print("Chat Result:", chat_response.json())
