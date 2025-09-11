# In your tasks.py or analysis module
import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import Client
from sentence_transformers import SentenceTransformer # <-- Import this
# --- NEW: Load environment variables and configure genai here ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # This will stop the program if the key is missing, which is good practice.
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)
# --- END NEW ---

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 50) -> list[str]:
    """Splits a long text into smaller, overlapping chunks."""
    if not text:
        return []
    words = text.split()
    chunks = []
    # Use a sliding window to create chunks
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks


# In your tasks.py or analysis module

async def create_and_store_embeddings_manually_gemini(supabase: Client, meeting_id: str, transcript_text: str):
    """
    Chunks a transcript, creates embeddings, stores them, and updates the meeting status.
    """
    try:
        print(f"Starting manual embedding creation for meeting {meeting_id}...")
        
        chunks = chunk_text(transcript_text)
        if not chunks:
            print("No text to create embeddings for. Skipping.")
            return

        embedding_model = 'text-embedding-004'
        result = genai.embed_content(
            model=embedding_model,
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=1536  # Ensure this matches your embedding model's output size
        )
        embeddings = result['embedding']

        records_to_insert = [{
            "meeting_id": meeting_id,
            "content": chunk,
            "embedding": embeddings[i]
        } for i, chunk in enumerate(chunks)]

        supabase.table("meeting_embeddings").insert(records_to_insert).execute()
        
        print(f"Successfully created and stored {len(records_to_insert)} embeddings for meeting {meeting_id}")

        # --- ✅ ADD THIS STEP ---
        # After successfully storing embeddings, update the meeting's status flag.
        supabase.table("meetings").update({"embedding_created": True}).eq("id", meeting_id).execute()
        print(f"Updated 'embedding_created' flag to True for meeting {meeting_id}")
        # --- END OF ADDED STEP ---

    except Exception as e:
        print(f"Error creating embeddings manually for meeting {meeting_id}: {e}")




async def create_and_store_embeddings_manually(supabase: Client, meeting_id: str, transcript_text: str):
    """
    Chunks a transcript, creates embeddings, stores them, and updates the meeting status.
    """
    try:
        print(f"Starting manual embedding creation for meeting {meeting_id}...")
        
        chunks = chunk_text(transcript_text)
        if not chunks:
            print("No text to create embeddings for. Skipping.")
            return
        
        embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')

        embeddings = embedding_model.encode(chunks, show_progress_bar=True,normalize_embeddings=True).tolist()

        records_to_insert = [{
            "meeting_id": meeting_id,
            "content": chunk,
            "embedding": embeddings[i]
        } for i, chunk in enumerate(chunks)]

        supabase.table("meeting_embeddings").insert(records_to_insert).execute()

        print(f"Successfully created and stored {len(records_to_insert)} embeddings for meeting {meeting_id}")

        # --- ✅ ADD THIS STEP ---
        # After successfully storing embeddings, update the meeting's status flag.
        supabase.table("meetings").update({"embedding_created": True}).eq("id", meeting_id).execute()
        print(f"Updated 'embedding_created' flag to True for meeting {meeting_id}")
        # --- END OF ADDED STEP ---
    except Exception as e:
        print(f"Error creating embeddings manually for meeting {meeting_id}: {e}")