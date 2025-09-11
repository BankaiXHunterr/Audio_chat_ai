# In a file like utility.py

import requests
import time
import google.generativeai as genai
from supabase import Client
import os
from backend.modules.utility.gemini_file_api_uploader import FileUploader
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
file_uploader = FileUploader(
    upload_url="https://generativelanguage.googleapis.com/upload/v1beta/files",
    api_key=GOOGLE_API_KEY
)

def upload_file_to_gemini(audio_content: bytes, content_type: str, display_name: str) -> tuple[str | None, str | None]:
    """Uploads raw audio bytes to the Gemini File API and returns the URI and MIME type."""
    print("Uploading file to Gemini File API...")

    headers = {
        "Content-Type": content_type,
        "x-goog-api-key": GOOGLE_API_KEY
    }

    file_uploader.upload_file()
    
    # response = requests.post(url, headers=headers, data=audio_content)
    
    if response.status_code == 200:
        file_data = response.json().get("file", {})
        print(f"File uploaded successfully. URI: {file_data.get('uri')}")
        return file_data.get("uri"), file_data.get("mimeType")
    else:
        print(f"File upload failed: {response.status_code} - {response.text}")
        return None, None

def check_file_status_is_active(file_uri: str, max_retries: int = 10, wait_time: int = 10) -> bool:
    """Polls the Gemini File API until the file state is ACTIVE."""
    headers = {"x-goog-api-key": GOOGLE_API_KEY}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(file_uri, headers=headers)
            response.raise_for_status()
            
            state = response.json().get('file', {}).get('state')
            print(f"Current file state: {state}")

            if state == 'ACTIVE':
                return True
            elif state in ['FAILED', 'EXPIRED']:
                print(f"File processing failed or expired: {state}")
                return False

        except requests.RequestException as e:
            print(f"An error occurred while checking file status: {e}")

        print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
        time.sleep(wait_time)
        
    print("Max retries reached. File is not active.")
    return False





