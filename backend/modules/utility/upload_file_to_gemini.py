# import requests
import os
import mimetypes
import time
import requests
from pathlib import Path    


class FileUploader:
    def __init__(self, upload_url, api_key):
        """
        Initializes the FileUploader with the API endpoint and key.
        """
        self.upload_url = upload_url
        self.api_key = api_key

    def upload_raw_bytes(self, file_content: bytes, mime_type: str, display_name: str) -> tuple[str | None, str | None]:
        """
        Uploads raw file content (bytes) directly to the Gemini File API.
        This is the correct method for this specific API endpoint.
        """
        # --- 1. Set up the required headers ---
        # The API uses headers to get metadata, not form fields.
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": mime_type,
            "x-goog-file-name": display_name,
        }

        # --- 2. Construct the full API URL ---
        full_url = f"{self.upload_url}?key={self.api_key}"
        
        # --- 3. Make the POST request with raw data ---
        try:
            print(f"Uploading '{display_name}' to Gemini API using raw byte transfer...")
            
            # --------------------- THE FIX IS HERE ---------------------
            # REMOVED: The 'files' dictionary and 'files=' parameter.
            # ADDED: The 'headers=' and 'data=' parameters.
            
            response = requests.post(
                full_url,
                headers=headers,
                data=file_content, # This sends the raw binary content.
                timeout=600
            )
            # ---------------------------------------------------------
            
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

            # --- 4. Parse the JSON response ---
            upload_data = response.json()
            
            file_uri = upload_data.get('file', {}).get('uri')
            response_mime_type = upload_data.get('file', {}).get('mimeType')

            if not file_uri:
                print("Upload succeeded, but no file URI was found in the response.")
                return None, None
            
            print(f"File uploaded successfully. URI: {file_uri}")
            return file_uri, response_mime_type

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error during file upload: {e.response.status_code} - {e.response.text}")
            return None, None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during file upload: {e}")
            return None, None
        

    def check_file_status(self,file_uri, max_retries=10, wait_time=5):
        status_url = file_uri  # The file URI can be used to check its status
        headers = {
            "x-goog-api-key": self.api_key
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(status_url, headers=headers)  # Set verify=True in production
                response.raise_for_status()  # Raise an error for bad responses

                file_info = response.json()
                state = file_info.get('state')
                print(f"Current file state: {state}")

                if state == 'ACTIVE':
                    return True
                elif state in ['FAILED', 'EXPIRED']:
                    print(f"File processing failed or expired: {state}")
                    return False

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")  # Log HTTP errors
            except requests.exceptions.RequestException as req_err:
                print(f"Request error occurred: {req_err}")  # Log other request errors
            except Exception as e:
                print(f"An unexpected error occurred: {e}")  # Log unexpected errors

            # Wait before checking again
            print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

        print("Max retries reached. File status could not be determined.")
        return False
