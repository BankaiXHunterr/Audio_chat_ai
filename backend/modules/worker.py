import os
import time
from datetime import datetime
from multiprocessing import Process
from supabase import Client, create_client
import json
import asyncio
from supabase import Client, create_client
from dotenv import load_dotenv
import google.api_core.exceptions

# Make sure to import the actual analysis function
from modules.utility.transcript_generator import analyze_audio_with_gemini_tools

load_dotenv()

# --- Configuration for the worker process ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def process_meeting_job(job: dict, results_queue):
    """
    This function is called by the worker. It's synchronous, but it will
    run the async analysis function inside an asyncio event loop.
    """
    # Initialize a new Supabase client *inside* the worker function
    # This is crucial for multiprocessing safety
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Correctly unpack the job data
    meeting_id = job.get("meeting_id")
    user_id = job.get("user_id")
    # recording_contents = job.get("recording_contents")
    temp_file_path = job.get("temp_file_path")
    recording_content_type = job.get("recording_content_type")
    recording_url = job.get("recording_url")


    if not temp_file_path or not os.path.exists(temp_file_path):
        raise ValueError(f"Worker Error: Temporary file path not provided or file does not exist at '{temp_file_path}'")



    print(f"⚙️ Worker picked up job for meeting: {meeting_id}")

    try:

        with open(temp_file_path,'rb') as f:
            recording_contents = f.read()

        # Mark the meeting as 'processing'
        supabase.table("meetings").update({"status": "processing"}).eq("id", meeting_id).execute()

        # --- AI Analysis with Key Rotation ---
        api_keys_str = os.getenv("GEMINI_API_KEYS", "")
        if not api_keys_str:
            raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
        
        api_keys = [key.strip() for key in api_keys_str.split(',')]
        
        analysis_successful = False
        last_error = None

        for key in api_keys:
            try:
                print(f"🤖 Attempting analysis for meeting {meeting_id} with a new API key...")
                # Run the async function within the synchronous worker

                asyncio.run(analyze_audio_with_gemini_tools(
                    supabase=supabase,
                    meeting_id=meeting_id,
                    audio_content=recording_contents,
                    content_type=recording_content_type,
                    api_key=key
                ))
                analysis_successful = True
                print(f"✅ Analysis successful for meeting {meeting_id}!")
                break
            except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
                print(f"API key failed. Trying next key. Reason: {type(e).__name__}")
                last_error = e
                continue
            except Exception as e:
                print(f"An unexpected error occurred during analysis: {e}")
                last_error = e
                continue

        if not analysis_successful:
            raise Exception(f"All Gemini API keys failed. Last error: {last_error}")

        # The 'meetings' table status is updated inside analyze_audio_with_gemini_tools
        # We just need to notify the main process that it's done.
        results_queue.put({"meetingId": meeting_id, "userId": user_id, "status": "completed"})

    except Exception as e:
        print(f"❌ Job failed for meeting {meeting_id}: {e}")
        supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
        results_queue.put({"meetingId": meeting_id, "userId": user_id, "status": "failed"})

