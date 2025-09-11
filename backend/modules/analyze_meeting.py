# In your new module file (e.g., tasks.py)
import json
# from ICICI.backend.modules.utils.gemini import API_KEY_GEMINI
import google.generativeai as genai
from supabase import Client
import requests
from fastapi import BackgroundTasks
import os
# import socketio

from backend.modules.utility.gemini_file_api_uploader import FileUploader
from dotenv import load_dotenv
from utility.utility import check_if_file_is_active
from prompt.tool_prompt import dirization_prompt
from prompt.tools import dirization_tool
import time


# --- 1. Configuration ---
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
model_name = os.getenv("MODEL_NAME", "gemini-1.5-flash")
GEMINI_FILE_UPLOAD_API_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
api_end_point = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

file_path = r"D:\m32_ai\backend\audio\STOP Answering IELTS Speaking Questions Like This.mp3"

if not os.path.exists(file_path):
    raise ValueError("File not found")


uploader = FileUploader(GEMINI_FILE_UPLOAD_API_URL, GOOGLE_API_KEY)

# file_uri , mime_type = uploader.upload_file(path)

header = {
    "x-goog-api-key":GOOGLE_API_KEY
}


def check_file_status(file_uri, api_key, max_retries=10, wait_time=5):
    status_url = file_uri  # The file URI can be used to check its status
    headers = {
        "x-goog-api-key": api_key
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(status_url, headers=headers, verify=False)  # Set verify=True in production
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



file_uri, mime_type = uploader.upload_file(file_path=file_path)

if check_if_file_is_active(file_uri=file_uri,header=header):


# Construct payload for generateContent API  

# if check_file_status(file_uri=file_uri,api_key=API_KEY_GEMINI):

    gemini_payload = {  
    "contents": [  
        {  
            "role": "user",  
            "parts": [  
                {  
                    "fileData": {  
                        "fileUri": file_uri,  
                        "mimeType": mime_type  
                    }

                },
                {  
                    "text": dirization_prompt
                } 
            ]  
        }  
    ],
    "tools":[
        {
            "function_declarations": [dirization_tool]  # Ensure tool1 is defined in your context
            }
        ],
    "tool_config":{
        "function_calling_config":{"mode":"ANY"},
    }
    } 

    header = {
    "x-goog-api-key":GOOGLE_API_KEY,
    "Content-Type":"application/json"}

    try:
        start = time.time()
        response = requests.post(api_end_point,headers=header,
                                    json=gemini_payload,
                                    verify=False,
                                    timeout=600)
        
        print(response.text)
        if response.status_code == 200:
            response_dict = response.json()

            response_object = response_dict.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("functionCall", []).get("args", {})
            print(response_object)

            transcript = response_object.get("transcript", [])
            summary = response_object.get("summary", "")
            keyHighlights = response_object.get("keyHighlights", [])
            actionItems = response_object.get("actionItems", [])


            with open("D:\\m32_ai\\backend\\response.json", "w") as f:
                json.dump(response_dict, f, indent=2)
            # print(json.dumps(response_dict, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")