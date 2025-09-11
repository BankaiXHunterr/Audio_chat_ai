# In your generate_embedding.py file (or wherever create_and_store_embeddings_manually resides)
import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import Client
from sentence_transformers import SentenceTransformer
import google.api_core.exceptions

load_dotenv()

# --- NEW: Function for chunking text (no changes needed) ---
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Splits a long text into smaller, overlapping chunks."""
    if not text:
        return []
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

# --- UPDATED: create_and_store_embeddings_manually with key rotation ---
async def create_and_store_embeddings_manually(supabase: Client, meeting_id: str, transcript_text: str):
    """
    Chunks a transcript, creates embeddings with API key rotation,
    stores them, and updates the meeting status.
    """
    # Load all API keys from the .env file
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    if not api_keys_str:
        raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
    api_keys = [key.strip() for key in api_keys_str.split(',')]

    try:
        print(f"Starting manual embedding creation for meeting {meeting_id}...")
        
        chunks = chunk_text(transcript_text)
        if not chunks:
            print("No text to create embeddings for. Skipping.")
            return

        embedding_model = 'text-embedding-004'
        embeddings_result = None
        last_error = None

        # Loop through each key and try to perform the analysis
        for key in api_keys:
            try:
                print(f"Attempting embedding creation for meeting {meeting_id} with a new API key...")
                # Configure the generative AI client with the current key
                genai.configure(api_key=key)
                embeddings_result = genai.embed_content(
                    model=embedding_model,
                    content=chunks,
                    task_type="RETRIEVAL_DOCUMENT",
                )
                print(f"Embedding creation successful with key ending in '...{key[-4:]}'.")
                break  # Exit the loop on success
            
            except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
                print(f"API key ending in '...{key[-4:]}' failed. Reason: {type(e).__name__}. Trying next key...")
                last_error = e
                continue # Move to the next key
            except Exception as e:
                print(f"An unexpected error occurred during embedding creation with key '...{key[-4:]}': {e}")
                last_error = e
                continue

        # If the loop finishes and embeddings were not created, it means all keys failed.
        if embeddings_result is None:
            raise Exception(f"All Gemini API keys failed for embedding creation. Last error: {last_error}") from last_error

        embeddings = embeddings_result['embedding']

        records_to_insert = [{
            "meeting_id": meeting_id,
            "content": chunk,
            "embedding": embeddings[i]
        } for i, chunk in enumerate(chunks)]

        supabase.table("meeting_embeddings").insert(records_to_insert).execute()
        
        print(f"Successfully created and stored {len(records_to_insert)} embeddings for meeting {meeting_id}")

        supabase.table("meetings").update({"embedding_created": True}).eq("id", meeting_id).execute()
        print(f"Updated 'embedding_created' flag to True for meeting {meeting_id}")

    except Exception as e:
        print(f"Error creating embeddings manually for meeting {meeting_id}: {e}")
        # The main.py caller handles the error, so we don't need to re-raise here.