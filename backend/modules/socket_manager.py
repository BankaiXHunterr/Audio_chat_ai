# Create a new file: backend/socket_manager.py

import socketio
from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client for authentication
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create an async Socket.IO server instance
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Wrap it in an ASGI application
socket_app = socketio.ASGIApp(sio)

# Dictionary to map session IDs (sid) to user IDs
sid_to_user = {}

@sio.event
async def connect(sid, environ, auth):
    """
    Handles a new client connection. This is where we perform authentication.
    """
    if not auth or 'token' not in auth:
        print(f"Connection rejected for {sid}: No token provided.")
        raise socketio.exceptions.ConnectionRefusedError('Authentication failed: No token provided.')

    token = auth['token']
    try:
        # Validate the JWT using Supabase
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if not user:
            raise Exception("Invalid token")

        # Authentication successful
        user_id = str(user.id)
        print(f"Socket connection successful for user {user_id} with sid {sid}")
        
        # Store the user's ID and join them to a private room
        sid_to_user[sid] = user_id
        await sio.enter_room(sid, user_id)
        
        # You can emit a confirmation event back to the client
        await sio.emit('authenticated', {'status': 'success'}, to=sid)

    except Exception as e:
        print(f"Connection rejected for {sid}: {e}")
        raise socketio.exceptions.ConnectionRefusedError('Authentication failed: Invalid token.')

@sio.event
async def disconnect(sid):
    """
    Handles a client disconnection.
    """
    if sid in sid_to_user:
        user_id = sid_to_user[sid]
        print(f"User {user_id} disconnected with sid {sid}")
        # Clean up the mapping
        del sid_to_user[sid]