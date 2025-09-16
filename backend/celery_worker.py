import os
import requests
import asyncio
import tempfile
from celery import Celery
from dotenv import load_dotenv
from supabase import create_client, Client
import google.api_core.exceptions
from modules.utility.transcript_generator import analyze_audio_with_gemini_tools
import mimetypes
from modules.utility.upload_file_to_gemini import ApiKeyException
load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL") # You'll get this from your Redis provider

# --- Initialize Celery ---
celery_app = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_track_started=True,
)

GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "").split(',')


# --- Helper function for notifications ---
def notify_frontend(userId, meetingId, status):
    """Makes an internal API call to the FastAPI server to trigger a WebSocket event."""
    try:
        api_url = os.getenv("API_BASE_URL") # e.g., https://audio-chat-ai.onrender.com
        internal_key = os.getenv("INTERNAL_API_KEY")
        print(f'Internal_API:{internal_key}')
        if not api_url or not internal_key:
            print("🔴 ERROR: API_BASE_URL or INTERNAL_API_KEY not set. Cannot send notification.")
            return

        response = requests.post(
            f"{api_url}/internal/notify",
            json={"userId": userId, "meetingId": meetingId, "status": status},
            headers={"Authorization": f"Bearer {internal_key}"},
            timeout=10 # Add a timeout
        )
        response.raise_for_status() # Raise an exception for bad status codes
        print(f"✅ Notification sent for meeting {meetingId} with status '{status}'.")
    except requests.exceptions.RequestException as e:
        print(f"🔴 FAILED to send notification for meeting {meetingId}: {e}")



@celery_app.task(name='process_meeting_task', bind=True, max_retries=3)
def process_meeting_task(self, job: dict):
    """
    Downloads a file from a URL, processes it with Gemini, and cleans up.
    Includes automatic retries for download or processing errors.
    """
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    meeting_id = job.get("meeting_id")
    user_id = job.get("user_id")
    recording_url = job.get("recording_url")
    recording_content_type = job.get("recording_content_type")

    # Guard clause: Fail immediately if no URL is provided.
    if not recording_url:
        print(f"🔴 FATAL ERROR: No recording_url provided for meeting {meeting_id}. Failing job.")
        supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
        notify_frontend(user_id, meeting_id, "failed")
        return

    # Securely create a temporary file that will be cleaned up automatically.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_f:
        temp_file_path = temp_f.name

    try:
        print(f"⚙️ Celery worker picked up job for meeting: {meeting_id}")
        print(f"⬇️ Downloading from: {recording_url}")

        # --- Download Logic ---
        # Use streaming to handle large files without consuming all available memory.
        with requests.get(recording_url, stream=True, timeout=300) as r:
            # Raise an error for bad responses (404, 500, etc.)
            r.raise_for_status() 
            with open(temp_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"✅ Download complete. File saved to: {temp_file_path}")

        # --- AI Processing Logic ---
        with open(temp_file_path, 'rb') as f:
            recording_contents = f.read()


        # recording_content_type,_ = mimetypes.guess_file_type(temp_file_path)
        supabase.table("meetings").update({"status": "processing"}).eq("id", meeting_id).execute()

        # api_keys_str = os.getenv("GEMINI_API_KEYS")
        # api_keys = [key.strip() for key in api_keys_str.split(',')]
        
        analysis_successful = False
        last_error = None

        for key in GEMINI_API_KEYS:
            try:
                print(f"🤖 Attempting analysis for meeting {meeting_id}... with Key:{key[-4:]}")
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
            except (google.api_core.exceptions.PermissionDenied,
                    google.api_core.exceptions.ResourceExhausted,
                    ApiKeyException,
                    requests.exceptions.HTTPError) as e:
                
                print(f"API key failed. Trying next key. Reason: {type(e).__name__}")
                last_error = e
                continue
        
        if not analysis_successful:
            raise Exception(f"All Gemini API keys failed. Last error: {last_error}")

        # If we reach here, the job is done. Notify the frontend.
        notify_frontend(user_id, meeting_id, "completed")
        return {"status": "completed", "meetingId": meeting_id, "userId": user_id}

    except Exception as e:
        print(f"❌ Job failed for meeting {meeting_id}: {e}. Retrying if possible...")
        
        # This will automatically retry the task (including the download)
        # after a delay. It will try up to `max_retries` (3) times.
        try:
            self.retry(exc=e, countdown=60)
        except Exception as retry_exc:
            # This block runs only after all retries have been exhausted.
            print(f"🔴 All retries failed for meeting {meeting_id}. Marking as failed. Final error: {retry_exc}")
            supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
            notify_frontend(user_id, meeting_id, "failed")
            
    finally:
        # This block always runs, ensuring the temporary file is deleted
        # whether the task succeeded, failed, or was retried.
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"🧹 Cleaned up temporary file: {temp_file_path}")
