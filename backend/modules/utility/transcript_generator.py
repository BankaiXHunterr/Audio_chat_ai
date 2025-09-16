# In your tasks.py or analysis module

from supabase import Client
# Import your updated FileUploader class
from modules.utility.utility import check_file_status
import os
from modules.prompt.tool_prompt import dirization_prompt
from modules.prompt.tools import dirization_tool
import requests
from dotenv import load_dotenv  
from modules.utility.upload_file_to_gemini import FileUploader
import json
from pathlib import Path
import time
load_dotenv()


# ... other imports

# --- Configuration ---
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_FILE_UPLOAD_API_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files" # Note: No /upload/ prefix
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
api_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"


async def analyze_audio_with_gemini_tools(
    supabase: Client,
    meeting_id: str,
    audio_content: bytes,
    content_type: str,
    api_key: str
):
    """
    Analyzes audio content using your FileUploader class.
    """

    # try:

    # --- Step 1: Upload the file using your class ---
    uploader = FileUploader(GEMINI_FILE_UPLOAD_API_URL, api_key)
    
    file_uri, mime_type = uploader.upload_raw_bytes(
        file_content=audio_content,
        mime_type=content_type,
        display_name=f"meeting_recording_{meeting_id}"
    )
    
    print(f"File uploaded: {file_uri} (MIME type: {mime_type})")
    
    if not file_uri:
        raise Exception("File upload failed using FileUploader.")

    # --- Step 2: Wait for the file to be active ---
    if not check_file_status(file_uri, api_key):
        raise Exception("File did not become active for processing.")
        
    # --- Step 3: Call Gemini's generateContent API ---

    gemini_payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"fileData": {"fileUri": file_uri, "mimeType": mime_type}},
                {"text": dirization_prompt}
            ]
        }],
        "tools": [{"function_declarations": [dirization_tool]}],
        "tool_config": {"function_calling_config": {"mode": "ANY"}}
    }


    header = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }
    while True:
        try:
            response = requests.post(api_endpoint, headers=header, json=gemini_payload)
            response.raise_for_status()  # Raise an error for HTTP errors

            # --- Step 4: Parse the response and save to database ---


            # If we get here, the request was successful (status 2xx)
            print("✅ Gemini analysis request successful.")
            break # Exit the loop

        except requests.exceptions.HTTPError as e:
            # --- THIS IS THE NEW LOGIC ---
            if e.response.status_code == 503:
                print("🚦 Model is overloaded (503). Waiting for 60 seconds before retrying...")
                time.sleep(60)
                continue # Retry the request
            else:
                # For any other HTTP error (like 400, 401), re-raise the exception
                # so the Celery worker can handle it (e.g., by trying the next key).
                print(f"🔴 A non-retriable HTTP error occurred: {e.response.status_code}")
                raise e
        except requests.exceptions.RequestException as e:
             print(f"🔴 A network-related error occurred: {e}")
             raise e
        

    response_dict = response.json()

    if "candidates" not in response_dict or not response_dict["candidates"]:
        # If not, the API likely returned an error or an empty response.
        # We log the entire response to see what went wrong.
        print("🔴 ERROR: 'candidates' key not found in Gemini response.")
        print("Full API Response:", json.dumps(response_dict, indent=2))
        raise ValueError("Invalid response structure from Gemini API.")
    
    # Safely access nested keys
    first_candidate = response_dict["candidates"][0]
    
    if "content" not in first_candidate or "parts" not in first_candidate["content"]:
        print("🔴 ERROR: 'content' or 'parts' not in the first candidate.")
        print("Full API Response:", json.dumps(response_dict, indent=2))
        raise ValueError("Unexpected response format from Gemini: missing content parts.")


    # Extract the function call arguments
    function_call = first_candidate["content"]["parts"][0].get("functionCall")
    if not function_call or "args" not in function_call:
        print("🔴 ERROR: 'functionCall' or 'args' not found in the response part.")
        print("Full API Response:", json.dumps(response_dict, indent=2))
        raise ValueError("Gemini response did not contain a function call.")

    function_args = function_call["args"]

    meeting_details_data = {
        "id": meeting_id,
        "transcript": function_args.get("transcript"),
        "summary": function_args.get("summary"),
        "key_highlights": function_args.get("keyHighlights"),
        "actionable_items": function_args.get("actionItems")
    }

    # print(meeting_details_data)

    supabase.table("meeting_details").insert(meeting_details_data).execute()
    
    # # --- Step 5: Update the original meeting's status ---
    supabase.table("meetings").update({"status": "completed"}).eq("id", meeting_id).execute()
    print(f"✅ Successfully analyzed and saved details for meeting {meeting_id}")
    # except Exception as e:
    # #     print(f"Error during background analysis for meeting {meeting_id}: {e}")
    # #     supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()


    # except requests.exceptions.HTTPError as http_err:
    #     # This will catch HTTP errors (like 400, 500) and print the response body.
    #     print(f"🔴 HTTP Error during Gemini analysis: {http_err}")
    #     print("Error Response:", http_err.response.text)
    #     raise # Re-raise the exception to be caught by the Celery worker
    # except Exception as e:
    #     print(f"🔴 An unexpected error occurred during analysis: {e}")
    #     raise