import os
import time
import requests
import json
import mimetypes
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- 1. Configuration ---

# Load keys from .env file. Ensure your .env file has a line like:
# GEMINI_API_KEYS="key1,key2,key3"
api_keys_env = os.getenv("GEMINI_API_KEYS")
if not api_keys_env:
    raise ValueError("🔴 GEMINI_API_KEYS not found in your .env file. Please add it.")

# Split the comma-separated keys into a list
API_KEYS_TO_TEST = [key.strip() for key in api_keys_env.split(",")]

print(f"🔑 Found {len(API_KEYS_TO_TEST)} API key(s) to test.")

# --- Models and API Configuration ---
MODEL_NAME = "gemini-1.5-flash"
GEMINI_FILE_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_FILE_UPLOAD_API_URL = f"{GEMINI_FILE_API_BASE_URL}/files:upload"
API_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

# --- Define the audio file you want to test ---
FILE_PATH = r"D:\m32_ai\Artificial Intelligence in 2 Minutes _ What is Artificial Intelligence_ _ Edureka [UFDOY1wOOz0].mp3"

if not os.path.exists(FILE_PATH):
    raise ValueError(f"🔴 File not found at: {FILE_PATH}. Please update the FILE_PATH variable.")

# --- 2. File Uploader Class ---
class FileUploader:
    def __init__(self, upload_url: str):
        self.upload_url = upload_url

    def upload_file(self, file_path: str, api_key: str) -> tuple[str | None, str | None, str | None]:
        print(f"\n🚀 Attempting to upload file with key ending in '...{api_key[-4:]}'")
        
        mime_type, _ = mimetypes.guess_type(file_path)
        print(f"   - Detected MIME Type: {mime_type}")
        if mime_type is None:
            print(f"   - 🔴 Could not determine MIME type for {file_path}")
            return None, None, None
            
        with open(file_path, "rb") as f:
            file_content = f.read()

        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }
        
        request_body = {
            "file": {
                "display_name": os.path.basename(file_path)
            }
        }
        
        # Use simple POST to get the upload URL
        try:
            # This is the correct new upload flow, first request gets an upload URL
            initial_response = requests.post(
                f"{GEMINI_FILE_API_BASE_URL}/files?key={api_key}",
                headers=headers,
                json=request_body
            )
            initial_response.raise_for_status()
            upload_info = initial_response.json()
            file_name = upload_info.get('file', {}).get('name')
            upload_uri = upload_info.get('file', {}).get('uri')


            # Now upload the actual file bytes
            upload_headers = {
                 "x-goog-api-key": api_key,
                'Content-Type': mime_type
            }
            upload_response = requests.post(
                upload_uri, headers=upload_headers, data=file_content
            )
            upload_response.raise_for_status()

            print(f"   - ✅ File uploaded successfully. File Name: {file_name}")
            return file_name, mime_type, upload_uri

        except requests.exceptions.RequestException as e:
            print(f"   - 🔴 An error occurred during file upload: {e}")
            if e.response:
                print(f"   - Response Body: {e.response.text}")
            return None, None, None

# --- 3. File Status Checker ---
def check_file_status(file_name: str, api_key: str, max_retries: int = 20, wait_time: int = 10) -> bool:
    """Polls the Gemini File API until the file is ready or fails."""
    print(f"   - ⏳ Checking processing status for file: {file_name}")
    status_url = f"{GEMINI_FILE_API_BASE_URL}/{file_name}?key={api_key}"
    headers = {"x-goog-api-key": api_key}

    for attempt in range(max_retries):
        try:
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()

            state = response.json().get('file', {}).get('state')
            print(f"   - ⏳ Current state: {state} (Attempt {attempt + 1}/{max_retries})")

            if state == 'ACTIVE':
                print("   - ✅ File is now ACTIVE and ready for analysis.")
                return True
            elif state == 'FAILED':
                print(f"   - 🔴 File processing failed. Error: {response.json().get('file', {}).get('error')}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   - 🔴 An error occurred while checking file status: {e}")
            return False

        time.sleep(wait_time)

    print("   - 🔴 Max retries reached. File did not become active in time.")
    return False

# --- 4. Main Test Function ---
def test_api_key(api_key: str, uploader: FileUploader):
    """Tests a single API key."""
    print("-" * 60)
    
    file_name, mime_type, file_uri = uploader.upload_file(file_path=FILE_PATH, api_key=api_key)

    if not (file_name and mime_type and check_file_status(file_name, api_key)):
        print(f"🔴 FAILED: API Key '...{api_key[-4:]}' - Could not process the file.")
        return

    print("\n   - 🔬 File is active. Sending for analysis...")
    gemini_payload = {
        "contents": [{"parts": [{"file_data": {"mime_type": mime_type, "file_uri": file_uri}}]}]
    }

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=gemini_payload, timeout=600)
        response.raise_for_status()
        
        response_dict = response.json()
        if "candidates" in response_dict:
            print(f"✅ SUCCESS: API Key '...{api_key[-4:]}' is working correctly!")
        else:
            print(f"🔴 FAILED: API Key '...{api_key[-4:]}' - Analysis request failed. Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"🔴 FAILED: API Key '...{api_key[-4:]}' - An error occurred during analysis: {e}")
        if e.response:
            print(f"   - Response Body: {e.response.text}")

# --- 5. Execution Logic ---
if __name__ == "__main__":
    if not API_KEYS_TO_TEST:
        print("🔴 No API keys found to test. Please check your .env file.")
    else:
        file_uploader = FileUploader(GEMINI_FILE_UPLOAD_API_URL)
        for key in API_KEYS_TO_TEST:
            test_api_key(key, file_uploader)