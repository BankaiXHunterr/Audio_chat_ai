from email.mime import message
import os
from turtle import title
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from modules.utility.transcript_generator import analyze_audio_with_gemini_tools
import google.generativeai as genai

import bcrypt
import postgrest.exceptions
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, Form, File, UploadFile, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from supabase import Client, create_client
import json
from gotrue.errors import AuthApiError # Add this import
from fastapi import BackgroundTasks # Add this import
from modules.generate_embedding import create_and_store_embeddings_manually
from modules.ai_response import get_rag_response
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel
from typing import List, Optional
from modules.utility.utility import enrich_participants
import time
from modules.socket_manager import sio, socket_app
import socketio
import google.api_core.exceptions
from modules.utility.pydantic_model import *
from multiprocessing import Process, Manager, Queue
import asyncio
import pathlib
from multiprocessing import Process, Manager
from typing import Annotated
from modules.worker import process_meeting_job
from contextlib import asynccontextmanager
# from pydub import AudioSegment
import io
import tempfile
from celery_worker import celery_app, process_meeting_task


TEMP_DIR = pathlib.Path("./temp_recordings").resolve()
TEMP_DIR.mkdir(exist_ok=True)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

# --- Basic Setup ---
load_dotenv()



# # --- Multiprocessing Worker Setup ---
# def worker_main_loop(task_queue: Queue, results_queue: Queue):
#     """The main loop for the worker process."""
#     print(f"✅ Worker process started (PID: {os.getpid()}).")
#     while True:
#         try:
#             job = task_queue.get()
#             process_meeting_job(job, results_queue)
#         except (KeyboardInterrupt, SystemExit):
#             break
#         except Exception as e:
#             print(f"Error in worker main loop: {e}")

# # --- Real-time Notification Listener ---
# async def listen_for_results(results_queue: Queue):
#     """Checks the results queue and sends socket notifications."""
#     print("🚀 Result listener started.")
#     while True:
#         if not results_queue.empty():
#             result = results_queue.get()

#             print(f"[listen_for_results][line-88] got following payload for websocket:{result}")

#             await sio.emit(
#                 'meeting_processing_complete',
#                 {'meetingId': result['meetingId'], 'status': result['status']},
#                 room=result['userId']
#             )
#         await asyncio.sleep(1)



# # --- 3. FastAPI Lifespan Manager (Modern Replacement for on_event) ---
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # This code runs on startup
#     print("🚀 Application starting up...")
#     manager = Manager()
#     task_queue = manager.Queue()
#     results_queue = manager.Queue()
    
#     app.state.task_queue = task_queue
    
#     worker = Process(target=worker_main_loop, args=(task_queue, results_queue))
#     worker.daemon = True
#     worker.start()
#     app.state.worker_process = worker
    
#     asyncio.create_task(listen_for_results(results_queue))
    
#     yield # The application is now running
    
#     # This code runs on shutdown
#     print("👋 Application shutting down...")
#     app.state.worker_process.terminate()
#     app.state.worker_process.join()


# app = FastAPI(lifespan=lifespan)
app = FastAPI()
app.mount("/socket.io", socket_app)
# --- ADD THIS CORS MIDDLEWARE CONFIGURATION ---
origins = [
    "https://audio-chat-ai.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)


# Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)




# --- JWT & OAuth2 Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", SECRET_KEY)  # Separate key for refresh tokens
# This tells FastAPI which URL will be used to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ========================================================================
# CONSTANTS
# ========================================================================

MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "video/mp4", "video/quicktime"]



# ========================================================================
# BACKGROUND TASK FUNCTION
# ========================================================================



# --- JWT Helper Function ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration of 15 minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# NEW: Function to create refresh tokens
def create_refresh_token(data: dict):
    """Creates a new JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



# --- User Verification Dependency ---
# --- User Verification Dependency ---
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Validates the Supabase JWT and returns the user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Use the Supabase client to verify the token and get user data
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        
        if not user:
            raise credentials_exception
        
        # Now, fetch the user's profile from your 'profiles' table
        profile_response = supabase.table("profiles").select("*").eq("id", user.id).execute()
        
        if not profile_response.data:
            # This is a fallback, in case the profile wasn't created
            # You can return the auth user data directly
            return {"id": user.id, "email": user.email}

        # Combine auth data and profile data for a complete user object
        full_user_profile = profile_response.data[0]
        full_user_profile['email'] = user.email # Add email from auth user
        return full_user_profile

    except (AuthApiError, Exception):
        raise credentials_exception

# --- API Endpoints ---

@app.post("/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
):
    try:
        # Sign up the user and pass names as metadata
        # The database trigger will use this metadata to create the profile
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "firstName": firstName,
                    "lastName": lastName,
                    "email": email
                }
            }
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Could not register user.")

        return {
            "message": f"Please check your email for confirmation."
        }

    except postgrest.exceptions.APIError as e:
        # This can happen if the email already exists in auth.users
        raise HTTPException(status_code=409, detail=f"Database Error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    


@app.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        # Use Supabase's built-in sign-in method
        # This handles password verification and returns a session with tokens
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password,
        })
        
        session = auth_response.session

        if not session:
            raise HTTPException(status_code=401, detail="Login failed, no session created.")
        
# --- START MODIFICATION ---
        
        # Step 2: Fetch the user's profile from your 'profiles' table
        user_id = session.user.id
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        
        if not profile_response.data:
            # This can happen if the profile wasn't created, handle gracefully
            raise HTTPException(status_code=404, detail="User authenticated but profile not found.")
        
        # Step 3: Combine tokens and profile into a single response
        return {
            "tokens": {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "token_type": "bearer",
                "expires_in": session.expires_in
            },
            "user": profile_response.data
        }

        # return {
        #     "access_token": session.access_token,
        #     "refresh_token": session.refresh_token,
        #     "token_type": "bearer"
        # }
        
    except AuthApiError as e:
        # Catch specific Supabase auth errors (e.g., invalid login credentials)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message or "Incorrect email or password",
        )
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.get("/users/me")
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    A protected endpoint that returns the current authenticated user's info.
    """
    # The dependency has already validated the token and fetched the user.
    # We can now safely return their data, excluding sensitive info.
    user_info = {
        "id": current_user.get("id"),
        "email": current_user.get("email"),
        "firstName": current_user.get("firstName"),
        "lastName": current_user.get("lastName"),
    }
    return user_info


@app.get("/")
async def health_check():
    return {"status": "ok"}



# ========================================================================
# MEETING MANAGEMENT API ENDPOINTS
# ========================================================================

# In main.py
@app.get("/meetings", response_model=PaginatedMeetingsResponse)
async def get_all_meetings(current_user: Annotated[dict, Depends(get_current_user)],page: int = 1,limit: int = 20):

    user_id = current_user.get("id")
    offset = (page - 1) * limit

    try:
        response = supabase.table("meetings").select("*", count='exact').eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        total_meetings = response.count
        processed_meetings = []

        for meeting in response.data or []:
            # Determine the display status
            proc_status = meeting.get("status")
            derived_status = "processing"
            if proc_status == 'failed':
                derived_status = 'failed'
            elif proc_status == 'completed':
                derived_status = 'completed'

            # Build a new, clean dictionary for each meeting
            processed_meetings.append(
                MeetingInList(
                    id=meeting.get("id"),
                    title=meeting.get("title", "Untitled Meeting"),
                    status=derived_status,
                    date=meeting.get("meeting_date"),
                    createdAt=meeting.get("created_at"),
                    participants=meeting.get("participants", []),
                    summary=meeting.get("summary", None)
                )
            )

        return {
            "meetings": processed_meetings,
            "total": total_meetings,
            "page": page,
            "limit": limit}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {e}")



@app.get("/meetings/{meeting_id}", response_model=MeetingDetail)
async def get_meeting_details(
    meeting_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Fetches the complete details for a single meeting, ensuring the user owns it.
    """
    user_id = current_user.get("id")
    str_meeting_id = str(meeting_id)

    try:
        # Fetch the meeting and its related details in one call
        response = supabase.table("meetings").select("*, meeting_details(*)").eq("id", str_meeting_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Meeting not found or you do not have permission.")

        meeting_data = response.data[0]
        details = meeting_data.pop('meeting_details', {}) or {}
        host = meeting_data.get("host", "Unknown Host")
        participant_emails = meeting_data.get("participants", [{"email": "", "name": "","role": ""}])
        # 2. Call the helper function to get the enriched list
        enriched_participants = await enrich_participants(supabase, host, participant_emails)
        # Derive the single status field
        proc_status = meeting_data.get("processing_status")
        derived_status = "processing"
        if proc_status == 'failed':
            derived_status = 'failed'
        elif proc_status == 'completed':
            derived_status = 'completed'


        # Construct the final response to match the frontend 'Meeting' interface
        return {
            "id": meeting_data.get("id"),
            "title": meeting_data.get("title"),
            "date": meeting_data.get("meeting_date"),
            "duration": meeting_data.get("duration"),
            "participants": enriched_participants,
            "recordingUrl": meeting_data.get("recording_url"),
            "createdAt": meeting_data.get("created_at"),
            "status": derived_status,
            "transcript": details.get("transcript"),
            "summary": details.get("summary"),
            "actionItems": details.get("actionable_items"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch meeting details: {e}")



# This is your updated, robust, non-blocking endpoint
@app.post("/meetings/process")
async def process_meeting(
    #  Use the request object to access the queue
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    recording: UploadFile = File(...),
    title: str = Form(...),
    date: str = Form(...),
    participants: str = Form("[]"),
):
    
    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(status_code=403, detail="User ID not found")

    # --- 1. Generate IDs and prepare initial data ---
    meeting_id = str(uuid.uuid4())
    file_extension = pathlib.Path(recording.filename).suffix
    participants_list = json.loads(participants)

    # --- 2. Create an initial meeting record with status 'uploading' ---
    initial_meeting_data = {
        "id": meeting_id,
        "user_id": user_id,
        "title": title,
        "meeting_date": date,
        "participants": participants_list,
        "status": "uploading", # Set initial status to 'uploading'
        "host": current_user.get("email", "Unknown Host"),
    }
    
    try:
        insert_response = supabase.table("meetings").insert(initial_meeting_data).execute()
        created_meeting = insert_response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create initial meeting record: {e}")

    # --- 3. Attempt to upload the file to Supabase Storage ---
    file_path = f"{user_id}/{meeting_id}{file_extension}"
    contents = await recording.read()

    try:
        print(f"Attempting to upload file to: {file_path}")
        supabase.storage.from_("recordings").upload(
            path=file_path,
            file=contents,
            file_options={"content-type": recording.content_type}
        )
        
        # --- 4a. On SUCCESSFUL upload ---
        recording_url = supabase.storage.from_("recordings").get_public_url(file_path)
        
        # Update the meeting record with the URL and 'uploaded' status
        supabase.table("meetings").update({
            "recording_url": recording_url,
            "status": "uploaded",
        }).eq("id", meeting_id).execute()
        
        print(f"✅ File uploaded successfully. Queuing job for analysis.")

        # Add the job to your multiprocessing queue for the worker to process
        # Assuming 'meeting_queue' is stored in app.state from a startup event
        job_data = {
            "meeting_id": meeting_id,
            "user_id": user_id,
            "recording_content_type": recording.content_type,
            "recording_url": recording_url,
        }

        # request.app.state.task_queue.put(job_data)
        process_meeting_task.delay(job_data)
        # Return the created meeting object to the frontend
        created_meeting['status'] = 'uploaded' # Ensure the returned object is up to date
        return {"meeting": created_meeting}

    except Exception as e:
        # --- 4b. On FAILED upload ---
        print(f"❌ Failed to upload file to storage: {e}")
        # Update the meeting record with 'failed' status
        supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
        # Return a erver error to the frontend
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")





@app.post("/meetings/chat")
async def chat_with_gemini(
    current_user: Annotated[dict, Depends(get_current_user)],
    message: str = Form(...),
    meeting_id: str = Form(...)   
):
    """
    Chat endpoint to interact with the Gemini model.
    """

    # 1. Execute the query to get the data
    is_embedding_created = supabase.table("meetings").select("*").eq("id", meeting_id).execute()
    print(f"Embedding check response: {is_embedding_created}")
    # 2. Check if data exists AND if the 'embedding_created' field is explicitly True
    if is_embedding_created.data and is_embedding_created.data[0].get("embedding_created"):
        print("Embeddings are already created. Proceeding to get RAG response...")
        resp = await get_rag_response(supabase, meeting_id, message)
        return {"response": resp}
        
    else:
        print("Embeddings have not been created yet. Proceeding with creation...")
        # Add your logic here to create the embeddings

        transcript_response = supabase.table("meeting_details").select("transcript").eq("id", meeting_id).execute()
        if not transcript_response.data:
            print("No transcript found for this meeting.")
            return {"response": f"No transcript available for meeting {meeting_id}"}

        transcript_list = transcript_response.data[0].get("transcript")
        transcript = "\n".join([f"[{item.get('timestamp')}] : {item.get('speaker')} --> {item.get('text')}" for item in transcript_list])
        await create_and_store_embeddings_manually(supabase, meeting_id, transcript)

        resp = await get_rag_response(supabase, meeting_id, message)
        return {"response": resp}


# highlight-start
@app.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: uuid.UUID, # Changed from Form(...) to a path parameter
    current_user: Annotated[dict, Depends(get_current_user)],
):
# highlight-end
    """
    Deletes a meeting, all its associated database records (via CASCADE),
    and its recording file from storage.
    """
    user_id = current_user.get("id")
    str_meeting_id = str(meeting_id)

    try:
        # --- 1. Fetch the meeting to get the recording_url ---
        # We must also check that the meeting belongs to the current user.
        select_response = supabase.table("meetings").select("recording_url").eq("id", str_meeting_id).eq("user_id", user_id).single().execute()

        if not select_response.data:
            # This handles cases where the meeting doesn't exist or the user doesn't own it.
            raise HTTPException(status_code=404, detail="Meeting not found or you do not have permission to delete it.")

        # --- 2. Delete the recording file from Supabase Storage ---
        recording_url = select_response.data.get("recording_url")
        if recording_url:
            # Extract the file path from the full URL.
            # Example URL: .../storage/v1/object/public/recordings/user_id/meeting_id.mp3
            # The path is the content after 'recordings/'
            try:
                # A more robust way to extract the path
                path_part = recording_url.split('/recordings/')[1]
                # The public URL might have query params, so we strip them
                file_path = path_part.split('?')[0]
                
                print(f"Deleting file from storage at path: {file_path}")
                supabase.storage.from_("recordings").remove([file_path])
            except IndexError:
                print(f"Could not parse file path from URL: {recording_url}")


        # --- 3. Delete the meeting record from the database ---
        # The ON DELETE CASCADE constraint will automatically delete all related rows
        # in `meeting_details`, `meeting_embeddings`, and `chats`.
        print(f"Deleting meeting record {str_meeting_id} from database...")
        delete_response = supabase.table("meetings").delete().eq("id", str_meeting_id).eq("user_id", user_id).execute()

        if not delete_response.data:
            # This is an extra safety check in case the delete failed after the file was removed.
            raise HTTPException(status_code=404, detail="Meeting not found or you do not have permission to delete it.")

        # A 204 No Content response is standard for a successful DELETE operation.
        # FastAPI handles this automatically because of the status_code in the decorator.
        return

    except Exception as e:
        print(f"An error occurred while deleting meeting {str_meeting_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete meeting.")



@app.post("/internal/notify")
async def send_notification(notification: Notification, request: Request):
    # Secure this endpoint
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {INTERNAL_API_KEY}":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    await sio.emit(
        'meeting_processing_complete',
        {'meetingId': notification.meetingId, 'status': notification.status},
        room=notification.userId
    )
    return {"message": "Notification sent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7888)

