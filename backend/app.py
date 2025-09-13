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
from fastapi import Depends, FastAPI, HTTPException, status, Form, File, UploadFile
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

import asyncio
import pathlib
from multiprocessing import Process, Manager
from typing import Annotated



# --- Basic Setup ---
load_dotenv()

app = FastAPI()
app.mount("/socket.io", socket_app)
# --- ADD THIS CORS MIDDLEWARE CONFIGURATION ---
origins = [
    # Add your frontend's URL here.
    # For development, allowing all origins is common.
    "*"
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
# MultiProcessing TASK FUNCTION
# ========================================================================




# --- Worker Process Function ---
def worker_process(task_queue, results_queue):
    """
    This function runs in a separate process. It waits for tasks and executes them.
    """
    print(f"Worker process started (PID: {os.getpid()}). Waiting for jobs...")
    # Re-initialize the Supabase client within the new process
    worker_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    while True:
        try:
            job = task_queue.get() # This will block until a job is available
            meeting_id = job['meeting_id']
            user_id = job['user_id']
            file_path = job['file_path']
            content_type = job['content_type']
            
            print(f"Worker picked up job for meeting: {meeting_id}")
            
            # --- Main Analysis Logic ---
            try:
                # Mark meeting as 'processing'
                worker_supabase.table("meetings").update({"status": "processing"}).eq("id", meeting_id).execute()
                
                # Read the temp file
                with open(file_path, "rb") as f:
                    recording_contents = f.read()
                
                # Run AI analysis (this is a placeholder for your function)
                # You'll need to make your analyze_audio_with_gemini_tools function synchronous
                # or run it within an asyncio event loop here if it's async.
                # For simplicity, we'll assume it's synchronous for this example.
                time.sleep(15) # Simulating a long AI task
                print(f"AI analysis complete for {meeting_id}")
                
                # Update details and status in Supabase
                worker_supabase.table("meeting_details").insert({"id": meeting_id, "summary": "AI summary..."}).execute()
                worker_supabase.table("meetings").update({"status": "completed"}).eq("id", meeting_id).execute()
                
                # Put the result on the results queue for notification
                results_queue.put({"meetingId": meeting_id, "userId": user_id, "status": "completed"})

            except Exception as e:
                print(f"Job failed for meeting {meeting_id}: {e}")
                worker_supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
                results_queue.put({"meetingId": meeting_id, "userId": user_id, "status": "failed"})

            finally:
                # Clean up the temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)

        except (KeyboardInterrupt, SystemExit):
            print("Worker process shutting down.")
            break
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(5)


# --- Real-time Notification Listener ---
async def listen_for_results(results_queue):
    """
    This runs in the main FastAPI event loop, checking the results queue.
    """
    print("Result listener started.")
    while True:
        if not results_queue.empty():
            result = results_queue.get()
            print(f"Got result from worker: {result}")
            await sio.emit(
                'meeting_processing_complete',
                {'meetingId': result['meetingId'], 'status': result['status']},
                room=result['userId']
            )
        await asyncio.sleep(1) # Check for results every second


# --- App Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    This function is called when the FastAPI application starts.
    It creates the shared queues and starts the worker process.
    """
    manager = Manager()
    task_queue = manager.Queue()
    results_queue = manager.Queue()
    
    # Store queues in the app state to be accessible by endpoints
    app.state.task_queue = task_queue
    app.state.results_queue = results_queue
    
    # Start the worker process
    p = Process(target=worker_process, args=(task_queue, results_queue))
    p.daemon = True # Allows the main process to exit even if the worker is running
    p.start()
    app.state.worker_process = p
    
    # Start the results listener as a background task
    asyncio.create_task(listen_for_results(results_queue))

# --- Your Existing Endpoints (Simplified) ---

# Your get_current_user, login, register, etc., endpoints remain the same...





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

# @app.get("/meetings", response_model=PaginatedMeetingsResponse)
# async def get_all_meetings(
#     current_user: Annotated[dict, Depends(get_current_user)],
#     page: int = 1,
#     limit: int = 20
# ):
#     """
#     Fetches a paginated list of all meetings for the current authenticated user.
#     """
#     user_id = current_user.get("id")
#     offset = (page - 1) * limit
    
#     try:
#         # response = supabase.table("meetings").select("*",count='exact').eq("user_id", user_id).order("meeting_date", desc=True).range(offset, offset + limit - 1).execute()
#         response = supabase.table("meetings").select("*", count='exact').eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()


#         # The total count is now part of the response
#         total_meetings = response.count

#         processed_meetings = []
#         for meeting in response.data or []:
#             proc_status = meeting.get("status")
            
#             # Derive a single status for the frontend
#             derived_status = "processing"
#             if proc_status == 'failed':
#                 derived_status = 'failed'
#             elif proc_status == 'completed':
#                 derived_status = 'completed'
            
#             # Enrich participants from list of emails to list of objects
#             enriched_participants = await enrich_participants(supabase, meeting.get("host"), meeting.get("participants", []))


#             meeting["id"] = meeting.get("id")
#             meeting["title"] = meeting.get("title", "Untitled Meeting")
#             meeting['status'] = derived_status
#             meeting['date'] = meeting.get('meeting_date') # Rename for consistency
#             meeting['createdAt'] = meeting.get('created_at') # Rename for consistency
#             meeting['participants'] = enriched_participants  # Ensure participants is always a list
#             meeting['summary'] = meeting.get('summary', None)  # Ensure summary is present
#             processed_meetings.append(meeting)

#         return {
#             "meetings": processed_meetings,
#             "total": total_meetings,
#             "page": page,
#             "limit": limit
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {e}")

# In main.py

@app.get("/meetings", response_model=PaginatedMeetingsResponse)
async def get_all_meetings(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = 1,
    limit: int = 20
):
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
            "limit": limit
        }
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



# This is your updated, non-blocking endpoint
# @app.post("/meetings/process")
# async def process_meeting(
#     background_tasks: BackgroundTasks,
#     current_user: Annotated[dict, Depends(get_current_user)],
#     recording: UploadFile = File(...),
#     title: str = Form(...),
#     date: str = Form(...),
#     participants: str = Form("[]"),
# ):
#     user_id = current_user.get("id")
#     print(f"[process_meeting][line-434] Got the following user id:{user_id}")
#     if not user_id:
#         raise HTTPException(status_code=403, detail="User ID not found")

#     # Read the file contents ONCE in the main endpoint.
#     # While this still takes time, it's unavoidable. The re-upload is what we're moving.
#     contents = await recording.read()
    
#     # --- 1. (FAST) Generate IDs and parse data ---
#     meeting_id = str(uuid.uuid4())
#     file_extension = recording.filename.split(".")[-1]
#     participants_list = json.loads(participants)

#     # --- 2. (FAST) Create the initial meeting record in the database ---
#     # The recording_url is left null for now. The status is 'processing'.
#     meeting_data = {
#         "id": meeting_id,
#         "user_id": user_id,
#         "title": title,
#         "meeting_date": date,
#         "participants": participants_list,
#         "status": "processing",
#         "host": current_user.get("email", "Unknown Host"),
#     }
    
#     print(f"[process_meeting][line-459] Got Following data for uploading to meeting table:{meeting_data}")
#     try:
#         insert_response = supabase.table("meetings").insert(meeting_data).execute()
#         created_meeting = insert_response.data[0]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create initial meeting record: {e}")

#     # --- 3. (FAST) Schedule ALL slow tasks to run in the background ---
#     background_tasks.add_task(
#         process_and_analyze_in_background,
#         supabase=supabase,
#         meeting_id=meeting_id,
#         user_id=user_id,
#         recording_contents=contents,
#         recording_content_type=recording.content_type,
#         file_extension=file_extension
#     )

#     # --- 4. (FAST) Return a response to the frontend immediately! ---
#     print(f"Immediately returning response for meeting {meeting_id}. Processing will continue in background.")
#     return {"meeting": created_meeting}

# In main.py

@app.post("/meetings/process")
async def process_meeting(
    current_user: Annotated[dict, Depends(get_current_user)],
    recording: UploadFile = File(...),
    title: str = Form(...),
    date: str = Form(...),
    participants: str = Form("[]"),
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="User ID not found")

    contents = await recording.read()
    meeting_id = str(uuid.uuid4())
    file_extension = recording.filename.split(".")[-1]
    file_path = f"{user_id}/{meeting_id}.{file_extension}"
    
    # 1. (FAST) Upload file to Supabase Storage
    try:
        supabase.storage.from_("recordings").upload(
            path=file_path,
            file=contents,
            file_options={"content-type": recording.content_type}
        )
        recording_url = supabase.storage.from_("recordings").get_public_url(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {e}")

    # 2. (FAST) Create the initial meeting record with 'uploaded' status
    meeting_data = {
        "id": meeting_id,
        "user_id": user_id,
        "title": title,
        "meeting_date": date,
        "participants": json.loads(participants),
        "status": "uploaded", # New initial status
        "recording_url": recording_url,
        "host": current_user.get("email", "Unknown Host"),
    }
    
    try:
        insert_response = supabase.table("meetings").insert(meeting_data).execute()
        created_meeting = insert_response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create initial meeting record: {e}")

    # 3. (FAST) Return immediately. The DB trigger will handle the rest.
    return {"meeting": created_meeting}



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



# # This new function will run entirely in the background
# async def process_and_analyze_in_background(
#     supabase: Client,
#     meeting_id: str,
#     user_id: str,
#     recording_contents: bytes,
#     recording_content_type: str,
#     file_extension: str
# ):
#     """
#     Handles the slow parts: uploading to storage and AI analysis.
#     """
#     file_path = f"{user_id}/{meeting_id}.{file_extension}"
    
#     try:
#         # --- 1. (BACKGROUND) Upload the audio file to Supabase Storage ---
#         print(f"Background Task: Uploading file to {file_path}...")
#         supabase.storage.from_("recordings").upload(
#             path=file_path,
#             file=recording_contents,
#             file_options={"content-type": recording_content_type}
#         )
        
#         # --- 2. (BACKGROUND) Get public URL and update the meeting record ---
#         recording_url = supabase.storage.from_("recordings").get_public_url(file_path)
        
#         supabase.table("meetings").update({
#             "recording_url": recording_url
#         }).eq("id", meeting_id).execute()

#         print(f"Background Task: Updated meeting {meeting_id} with recording URL.")


#         # Load all API keys from the .env file
#         api_keys_str = os.getenv("GEMINI_API_KEYS", "")
#         if not api_keys_str:
#             raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
        
#         api_keys = [key.strip() for key in api_keys_str.split(',')]

#         # --- 3. (BACKGROUND) Start the AI analysis ---
#         # This function is from your modules and does the heavy lifting
#         await analyze_audio_with_gemini_tools(
#             supabase,
#             meeting_id,
#             recording_contents,
#             recording_content_type
#         )
#                 # After successful analysis, send an update to the user
#         print(f"Processing complete for meeting {meeting_id}. Emitting update to user {user_id}.")
#         await sio.emit(
#             'meeting_processing_complete',
#             {'meetingId': meeting_id, 'status': 'completed'},
#             room=user_id  # Send the message only to the specific user
#         )
#         # highlight-end

#     except Exception as e:
#         # If anything fails, update the meeting status to 'failed'
#         print(f"Background task failed for meeting {meeting_id}: {e}")
#         supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
#         await sio.emit(
#             'meeting_processing_complete',
#             {'meetingId': meeting_id, 'status': 'failed'},
#             room=user_id
#         )
#         # highlight-end




# # This new function will run entirely in the background
# async def process_and_analyze_in_background(
#     supabase: Client,
#     meeting_id: str,
#     user_id: str,
#     recording_contents: bytes,
#     recording_content_type: str,
#     file_extension: str
# ):
#     """
#     Handles the slow parts: uploading to storage and AI analysis with API key rotation.
#     """
#     file_path = f"{user_id}/{meeting_id}.{file_extension}"
    
#     try:
#         # --- 1. (BACKGROUND) Upload the audio file to Supabase Storage ---
#         print(f"Background Task: Uploading file to {file_path}...")
#         supabase.storage.from_("recordings").upload(
#             path=file_path,
#             file=recording_contents,
#             file_options={"content-type": recording_content_type}
#         )
        
#         # --- 2. (BACKGROUND) Get public URL and update the meeting record ---
#         recording_url = supabase.storage.from_("recordings").get_public_url(file_path)
        
#         supabase.table("meetings").update({
#             "recording_url": recording_url
#         }).eq("id", meeting_id).execute()

#         print(f"Background Task: Updated meeting {meeting_id} with recording URL.")

#         # --- 3. (BACKGROUND) Start the AI analysis with retry logic ---
        
#         # Load all API keys from the .env file
#         api_keys_str = os.getenv("GEMINI_API_KEYS", "")
#         if not api_keys_str:
#             raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
        
#         api_keys = [key.strip() for key in api_keys_str.split(',')]
        
#         analysis_successful = False
#         last_error = None

#         # Loop through each key and try to perform the analysis
#         for key in api_keys:
#             try:
#                 print(f"Attempting analysis for meeting {meeting_id} with a new API key...")
#                 # Pass the key to the analysis function
#                 await analyze_audio_with_gemini_tools(
#                     supabase,
#                     meeting_id,
#                     recording_contents,
#                     recording_content_type,
#                     api_key=key  # Pass the current key from the loop
#                 )
#                 analysis_successful = True
#                 print(f"Analysis successful for meeting {meeting_id}!")
#                 break # Exit the loop on success
            
#             # Catch specific errors like permission denied or resource exhausted
#             except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
#                 print(f"API key ending in '...{key[-4:]}' failed. Reason: {type(e).__name__}. Trying next key...")
#                 last_error = e
#                 continue # Move to the next key
#             except Exception as e:
#                 # Catch any other unexpected error during analysis
#                 print(f"An unexpected error occurred during analysis with key '...{key[-4:]}': {e}")
#                 last_error = e
#                 # Depending on the error, you might want to retry or just fail
#                 # For this example, we'll try the next key
#                 continue

#         # If the loop finishes and analysis was not successful, it means all keys failed.
#         if not analysis_successful:
#             print("All API keys failed. Marking meeting as failed.")
#             # We re-raise the last known error to be caught by the outer exception handler
#             raise Exception(f"All Gemini API keys failed. Last error: {last_error}") from last_error

#         # After successful analysis, send an update to the user
#         print(f"Processing complete for meeting {meeting_id}. Emitting update to user {user_id}.")
#         await sio.emit(
#             'meeting_processing_complete',
#             {'meetingId': meeting_id, 'status': 'completed'},
#             room=user_id
#         )

#     except Exception as e:
#         # If anything fails (upload, DB update, or all API keys failed), update the status
#         print(f"Background task failed for meeting {meeting_id}: {e}")
#         supabase.table("meetings").update({"status": "failed"}).eq("id", meeting_id).execute()
#         await sio.emit(
#             'meeting_processing_complete',
#             {'meetingId': meeting_id, 'status': 'failed'},
#             room=user_id
#         )



# --- ADD THIS NEW INTERNAL ENDPOINT for notifications ---
@app.post("/internal/notify")
async def notify_client(notification: Notification):
    """
    An internal endpoint for the worker to call.
    It emits a socket event to the specified user.
    """
    print(f"Received notification from worker: {notification.dict()}")
    await sio.emit(
        'meeting_processing_complete',
        {'meetingId': notification.meetingId, 'status': notification.status},
        room=notification.userId
    )
    return {"status": "notification sent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7888)

