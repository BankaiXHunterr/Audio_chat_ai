# In your main.py or a utility file

import os
import uuid
from supabase import Client
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def retrieve_relevant_embeddings(
    supabase: Client,
    query: str,
    meeting_id: str
) -> list[str]:
    """
    Creates an embedding for a query and retrieves the most similar
    text chunks from the Supabase database.

    Args:
        supabase: The initialized Supabase client.
        query: The user's question or search term.
        meeting_id: The ID of the meeting to search within.

    Returns:
        A list of the most relevant text chunks.
    """
    try:
        # --- 1. Create an Embedding for the User's Query ---
        print(f"Creating embedding for query: '{query}'")
        embedding_model = 'text-embedding-004'
        
        # Use "RETRIEVAL_QUERY" for search queries
        query_embedding_result = genai.embed_content(
            model=embedding_model,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )
        query_embedding = query_embedding_result['embedding']

        # --- 2. Retrieve Similar Embeddings from Supabase via RPC ---
        # This calls the 'match_meeting_chunks' SQL function.
        print("Searching for relevant transcript chunks in Supabase...")
        match_response = supabase.rpc('match_meeting_chunks', {
            'query_embedding': query_embedding,
            'p_meeting_id': meeting_id,
            'match_threshold': 0.60, # How similar a chunk must be (0.0 to 1.0)
            'match_count': 5        # How many of the top chunks to return
        }).execute()
        
        if not match_response.data:
            print("No relevant chunks found.")
            return []
            
        # Extract just the text content from the results
        relevant_chunks = [item['content'] for item in match_response.data]
        print(f"Found {len(relevant_chunks)} relevant chunks.")
        
        return relevant_chunks

    except Exception as e:
        print(f"An error occurred while retrieving embeddings: {e}")
        return []

# --- EXAMPLE USAGE ---
# In a test script or your API endpoint, you would use it like this:

# supabase_client = create_client(URL, KEY)
# user_question = "What was the final decision on the budget?"
# target_meeting_id = "123e4567-e89b-12d3-a456-426614174000"

# relevant_context = retrieve_relevant_embeddings(
#     supabase=supabase_client,
#     query=user_question,
#     meeting_id=target_meeting_id
# )

# print("\n--- Most Relevant Context ---")
# for i, chunk in enumerate(relevant_context):
#     print(f"Chunk {i+1}: {chunk}\n")