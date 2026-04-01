from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import requests
import os
import tempfile

app = Flask(__name__)
CORS(app)

# Configuration
# Stability: Using gemini-2.0-flash which is widely available in 2026.
API_KEY = "AIzaSyAH2ApIovD_lpjqylOKC8BPsYLwXGHrW_g"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = secure_filename(file.filename)
    mime_type = file.content_type or "application/octet-stream"
    
    # Create temporary file to store the upload before sending to Google
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # 1. Initiate Resumable Upload
        init_headers = {
            "x-goog-api-key": API_KEY,
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(os.path.getsize(tmp_path)),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json"
        }
        init_body = {"file": {"display_name": filename}}
        
        init_response = requests.post(f"{UPLOAD_URL}?key={API_KEY}", 
                                    headers=init_headers, 
                                    json=init_body)
        
        if init_response.status_code != 200:
            return jsonify({"error": f"Failed to initiate upload: {init_response.text}"}), init_response.status_code
        
        upload_url = init_response.headers.get("X-Goog-Upload-URL")
        
        # 2. Upload actual file content
        with open(tmp_path, "rb") as f:
            upload_response = requests.post(
                upload_url,
                headers={
                    "X-Goog-Upload-Protocol": "resumable",
                    "X-Goog-Upload-Command": "upload, finalize",
                    "X-Goog-Upload-Offset": "0"
                },
                data=f
            )
        
        if upload_response.status_code not in [200, 201]:
            return jsonify({"error": f"Failed to upload file data: {upload_response.text}"}), upload_response.status_code
            
        file_uri = upload_response.json().get('file', {}).get('uri')
        return jsonify({"file_uri": file_uri, "mime_type": mime_type, "status": "success"})
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    file_uri = data.get('file_uri')
    file_mime = data.get('file_mime', 'application/pdf')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Payload construction
    parts = []
    if file_uri:
        parts.append({
            "fileData": {
                "mimeType": file_mime,
                "fileUri": file_uri
            }
        })
    parts.append({"text": user_message})
        
    payload = {
        "contents": [{
            "parts": parts
        }]
    }
    
    try:
        headers = {"x-goog-api-key": API_KEY}
        response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=120)
        response_data = response.json()
        
        if response.status_code != 200:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
            return jsonify({
                "error": response_data.get('error', {}).get('message', 'Unknown API error'),
                "status": "error"
            }), response.status_code
            
        # Extract text from response
        ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        return jsonify({
            "response": ai_text,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
