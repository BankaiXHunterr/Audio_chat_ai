# import os
# import time
# from datetime import datetime
# from multiprocessing import Process
# from supabase import Client, create_client
# import json
# import asyncio
# from supabase import Client, create_client
# from dotenv import load_dotenv
# import google.api_core.exceptions

# # Make sure to import the actual analysis function
# from modules.utility.transcript_generator import analyze_audio_with_gemini_tools

# load_dotenv()

# # --- Configuration for the worker process ---
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# def process_meeting_job(job: dict, results_queue):
#     """
#     This function is called by the worker. It's synchronous, but it will
#     run the async analysis function inside an asyncio event loop.
#     """
#     # Initialize a new Supabase client *inside* the worker function
#     # This is crucial for multiprocessing safety
#     supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

#     # Correctly unpack the job data
#     meeting_id = job.get("meeting_id")
#     user_id = job.get("user_id")
#     # recording_contents = job.get("recording_contents")
#     recording_url = job.get("recording_url")
#     recording_content_type = job.get("recording_content_type")

#     print(f"⚙️ Worker picked up job for meeting: {meeting_id}")

#     try:
#         # Mark the meeting as 'processing'
#         supabase.table("meetings").update({"status": "processing"}).eq("id", meeting_id).execute()

#         # --- ✨ NEW: Download the file from Supabase Storage ---
#         if not recording_url:
#             raise ValueError("Recording URL is missing from the job payload.")


#         # --- AI Analysis with Key Rotation ---
#         api_keys_str = os.getenv("GEMINI_API_KEYS", "")
#         if not api_keys_str:
#             raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
        
#         api_keys = [key.strip() for key in api_keys_str.split(',')]
        
#         analysis_successful = False
#         last_error = None

#         for key in api_keys:
#             try:
#                 print(f"🤖 Attempting analysis for meeting {meeting_id} with a new API key...")
#                 # Run the async function within the synchronous worker
#                 asyncio.run(analyze_audio_with_gemini_tools(
#                     supabase=supabase,
#                     meeting_id=meeting_id,
#                     audio_content=recording_contents,
#                     content_type=recording_content_type,
#                     api_key=key
#                 ))
#                 analysis_successful = True
#                 print(f"✅ Analysis successful for meeting {meeting_id}!")
#                 break
#             except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
#                 print(f"API key failed. Trying next key. Reason: {type(e).__name__}")
#                 last_error = e
#                 continue
#             except Exception as e:
#                 print(f"An unexpected error occurred during analysis: {e}")
#                 last_error = e
#                 continue

#         if not analysis_successful:
#             raise Exception(f"All Gemini API keys failed. Last error: {last_error}")

#         # The 'meetings' table status is updated inside analyze_audio_with_gemini_tools
#         # We just need to notify the main process that it's done.
#         results_queue.put({"meetingId": meeting_id, "userId": user_id, "status": "completed"})

#     except Exception as e:
#         print(f"❌ Job failed for meeting {meeting_id}: {e}")
#         supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
#         results_queue.put({"meetingId": meeting_id, "userId": user_id, "status": "failed"})




# # def worker_(queue,worker_id):
# #     while True:
# #         job = queue.get()
# #         try:
# #             process_meeting_job(job)
# #         except Exception as e:
# #             pass


# # def start_worker(queue,num_worker=1):
# #     workers = []
# #     for i in range(num_worker):
# #         p = Process(target=worker_,args=(queue,i+1))
# #         p.daemon = True
# #         p.start()
# #         workers.append(p)
    
# #     return workers




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
from urllib.parse import urlparse, unquote

# Make sure to import the actual analysis function
from modules.utility.transcript_generator import analyze_audio_with_gemini_tools

load_dotenv()

# --- Configuration for the worker process ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def process_meeting_job(job: dict, results_queue):
    """
    This function is called by the worker. It downloads the audio file from
    the provided URL and then runs the analysis.
    """
    # Initialize a new Supabase client *inside* the worker function
    # This is crucial for multiprocessing safety
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # --- ✨ CHANGE: Get URL instead of raw contents ---
    meeting_id = job.get("meeting_id")
    user_id = job.get("user_id")
    recording_url = job.get("recording_url") # Get the URL of the stored file
    recording_content_type = job.get("recording_content_type")

    # ❌ REMOVED: No longer receiving large file contents directly
    # recording_contents = job.get("recording_contents")

    print(f"⚙️ Worker picked up job for meeting: {meeting_id}")

    try:
        # Mark the meeting as 'processing'
        supabase.table("meetings").update({"status": "processing"}).eq("id", meeting_id).execute()

        # --- ✨ MODIFIED: Robustly parse the URL and download the file from Supabase Storage ---
        if not recording_url:
            raise ValueError("Recording URL is missing from the job payload.")

        try:
            # The public URL format is typically: .../storage/v1/object/public/recordings/file_path
            # We need to robustly extract the 'file_path' which includes the user_id and filename.
            # Using urlparse is safer than simply splitting the string.
            parsed_url = urlparse(recording_url)
            # Path might look like: /storage/v1/object/public/recordings/user_id/meeting_id.ext
            path_segments = parsed_url.path.strip('/').split('/')

            # Find the 'recordings' bucket segment and join everything after it.
            try:
                bucket_index = path_segments.index('recordings')
                file_path_encoded = '/'.join(path_segments[bucket_index + 1:])
                # URL-decode the path in case of spaces or special characters.
                file_path = unquote(file_path_encoded)
                if not file_path:
                    raise ValueError("Extracted file path from URL is empty.")
            except ValueError:
                raise ValueError("'recordings' bucket not found in the URL path.")

            print(f"Downloading file from storage path: {file_path}")
            
            # Download the file into memory for processing
            recording_contents = supabase.storage.from_("recordings").download(file_path)
            if not recording_contents:
                 raise Exception(f"Downloaded file content is empty for path: {file_path}")
        except Exception as e:
            # This catches both parsing and download errors.
            raise Exception(f"Failed to parse or download file from URL '{recording_url}'. Error: {e}")


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
                    audio_content=recording_contents, # Use the downloaded content
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

