from typing import List, Optional
from pydantic import BaseModel


# --- Pydantic Models (Data Shapes) ---
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token:str

class TokenData(BaseModel):
    email: str | None = None

# --- Pydantic Model for the request body ---
class ChatMessage(BaseModel):
    query: str

class LoginRequest(BaseModel):
    email: str
    password: str


# Add the new LoginRequest model to the response_model definition
class LoginResponse(BaseModel):
    tokens: Token
    user: dict

class MeetingInList(BaseModel):
    id: str
    title: str
    date: str
    status: str
    summary: Optional[str] = None # ADDED: Optional summary field
    participants: List[str] = []  # ADDED: List of participants
    createdAt: str # Added for sorting consistency


class PaginatedMeetingsResponse(BaseModel):
    meetings: List[MeetingInList]
    total: int
    page: int
    limit: int

class AllMeetingsResponse(BaseModel):
    meetings: List[MeetingInList]

class ParticipantDetail(BaseModel):
    email: str
    name: str
    role: Optional[str] = None  # e.g., 'host', 'attendee', etc.

class TranscriptSegment(BaseModel):
    speaker: str
    timestamp: str  # HH:MM:SS format
    text: str

class ActionItem(BaseModel):
    task: str
    assignee: str
    deadline: str  # Can be empty string if not mentioned
    status: str  # e.g., 'pending', 'completed', or empty string if not specified


# The MeetingDetail model remains the same
class MeetingDetail(BaseModel):
    id: str
    title: str
    date: str
    duration: Optional[int] = None
    participants: List[ParticipantDetail] = []  # List of participant objects with email and name
    transcript: Optional[List[TranscriptSegment]] = None
    summary: Optional[str] = None
    actionItems: Optional[List[ActionItem]] = None
    recordingUrl: Optional[str] = None
    status: str
    createdAt: str

class Notification(BaseModel):
    meetingId: str
    userId: str
    status: str