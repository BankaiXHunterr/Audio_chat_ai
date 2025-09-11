# # In your utility.py file

# import json
# import os
# import google.generativeai as genai
# import numpy as np
# import google.api_core.exceptions # <-- Import this for specific error handling
# from supabase import Client
# from dotenv import load_dotenv

# load_dotenv()

# # REMOVE the global configuration. We will configure it per-call now.
# # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# # genai.configure(api_key=GOOGLE_API_KEY)

# async def get_rag_response(
#     supabase: Client,
#     meeting_id: str,
#     user_query: str,
#     embedding_model: str = 'text-embedding-004',
#     generative_model: str = 'gemini-1.5-flash'
# ) -> str:
#     """
#     Performs a full RAG pipeline with retry logic for Gemini API calls.
#     """
#     # --- PREPARATION: Load API Keys ---
#     api_keys_str = os.getenv("GEMINI_API_KEYS", "")
#     if not api_keys_str:
#         raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
#     api_keys = [key.strip() for key in api_keys_str.split(',')]

#     # --- 1. Create query embedding with RETRY LOGIC ---
#     query_embedding_result = None
#     last_error = None

#     for key in api_keys:
#         try:
#             print(f"Attempting to create embedding with a new API key...")
#             genai.configure(api_key=key) # Configure with the current key
#             query_embedding_result = genai.embed_content(
#                 model=embedding_model,
#                 content=user_query,
#                 task_type="RETRIEVAL_QUERY",
#             )
#             print(f"Embedding created successfully with key ending in '...{key[-4:]}'.")
#             break # Success, exit the loop
#         except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
#             print(f"API key ending in '...{key[-4:]}' failed for embedding. Reason: {type(e).__name__}. Trying next key...")
#             last_error = e
#             continue
    
#     if query_embedding_result is None:
#         raise Exception(f"All API keys failed for embedding. Last error: {last_error}") from last_error

#     query_embedding = query_embedding_result['embedding']

#     # --- Steps 2, 3, 4, 5 (Finding relevant context) remain the same ---
#     # ... (your existing code for fetching chunks, calculating similarity, and sorting)
#     # ... (your existing code for retrieving chat history)
#     # ...
#     match_threshold = 0.44
#     match_count = 5
#     all_chunks_response = supabase.table("meeting_embeddings").select("content, embedding").eq("meeting_id", meeting_id).execute()
#     if not all_chunks_response.data:
#         return "I could not find any information for this meeting."
    
#     all_chunks = all_chunks_response.data
#     scored_chunks = []
#     for chunk in all_chunks:
#         chunk_vector = np.array(json.loads(chunk['embedding']), dtype=np.float32)
#         similarity = np.dot(query_embedding, chunk_vector)
#         scored_chunks.append({"content": chunk['content'], "similarity": similarity})
    
#     relevant_chunks = sorted([c for c in scored_chunks if c['similarity'] >= match_threshold], key=lambda x: x['similarity'], reverse=True)[:match_count]
#     relevant_context = [item['content'] for item in relevant_chunks]
    
#     history_response = supabase.table("chats").select("*").eq("meeting_id", meeting_id).order("created_at", desc=True).limit(10).execute()
#     chat_history = list(reversed(history_response.data))

#     # --- 6. Construct the prompt (remains the same) ---
#     chat_history_text = "\n".join([f"{c['sender'].upper()}: {c['message']}" for c in chat_history])
#     relevant_context_text = "\n---\n".join(relevant_context)
#     prompt = f"""You are a helpful meeting assistant. Answer the user's question based ONLY on the provided context below.
#     The context includes recent chat history and relevant sections of the meeting transcript. If the answer is not in the context, say so.

#     **Chat History:**
#     {chat_history_text}

#     **Relevant Transcript Sections:**
#     {relevant_context_text}

#     **User's New Question:**
#     {user_query}

#     **Your Answer:**
#     """
#     # --- 7. Generate the final answer with RETRY LOGIC ---
#     response = None
#     last_error = None

#     for key in api_keys:
#         try:
#             print(f"Attempting to generate response with a new API key...")
#             genai.configure(api_key=key) # Configure with the current key
#             model = genai.GenerativeModel(generative_model)
#             response = await model.generate_content_async(prompt)
#             print(f"Response generated successfully with key ending in '...{key[-4:]}'.")
#             break # Success, exit the loop
#         except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
#             print(f"API key ending in '...{key[-4:]}' failed for generation. Reason: {type(e).__name__}. Trying next key...")
#             last_error = e
#             continue

#     if response is None:
#         raise Exception(f"All API keys failed for generation. Last error: {last_error}") from last_error

#     return response.text.strip()

# # Note: Ensure you have the necessary imports and that your environment variables are set correctly.





# In your utility.py file

import json
import os
import google.generativeai as genai
import numpy as np
import google.api_core.exceptions
from supabase import Client
from dotenv import load_dotenv

load_dotenv()

async def get_rag_response(
    supabase: Client,
    meeting_id: str,
    user_query: str,
    embedding_model: str = 'text-embedding-004',
    generative_model: str = 'gemini-1.5-flash'
) -> str:
    """
    Performs a full RAG pipeline with retry logic for Gemini API calls,
    and stores the conversation in the database.
    """
    # --- PREPARATION: Load API Keys ---
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    if not api_keys_str:
        raise ValueError("GEMINI_API_KEYS environment variable not set or is empty.")
    api_keys = [key.strip() for key in api_keys_str.split(',')]

    # --- NEW: Save the user's message to the chat history table
    try:
        supabase.table("chats").insert({
            "meeting_id": meeting_id,
            "sender": "user",
            "message": user_query
        }).execute()
        print(f"User message saved for meeting {meeting_id}.")
    except Exception as e:
        # Don't fail the entire process if saving fails, but log the error
        print(f"Failed to save user message to chat history: {e}")

    # --- 1. Create query embedding with RETRY LOGIC ---
    query_embedding_result = None
    last_error_embedding = None

    for key in api_keys:
        try:
            print(f"Attempting to create embedding with a new API key...")
            genai.configure(api_key=key)
            query_embedding_result = genai.embed_content(
                model=embedding_model,
                content=user_query,
                task_type="RETRIEVAL_QUERY",
            )
            print(f"Embedding created successfully with key ending in '...{key[-4:]}'.")
            break
        except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
            print(f"API key ending in '...{key[-4:]}' failed for embedding. Reason: {type(e).__name__}. Trying next key...")
            last_error_embedding = e
            continue
    
    if query_embedding_result is None:
        raise Exception(f"All API keys failed for embedding. Last error: {last_error_embedding}") from last_error_embedding

    query_embedding = query_embedding_result['embedding']

    # --- Steps 2, 3, 4, 5 (Finding relevant context and retrieving chat history) ---
    match_threshold = 0.44
    match_count = 5
    all_chunks_response = supabase.table("meeting_embeddings").select("content, embedding").eq("meeting_id", meeting_id).execute()
    if not all_chunks_response.data:
        return "I could not find any information for this meeting."
    
    all_chunks = all_chunks_response.data
    scored_chunks = []
    for chunk in all_chunks:
        chunk_vector = np.array(json.loads(chunk['embedding']), dtype=np.float32)
        similarity = np.dot(query_embedding, chunk_vector)
        scored_chunks.append({"content": chunk['content'], "similarity": similarity})
    
    relevant_chunks = sorted([c for c in scored_chunks if c['similarity'] >= match_threshold], key=lambda x: x['similarity'], reverse=True)[:match_count]
    relevant_context = [item['content'] for item in relevant_chunks]
    
    history_response = supabase.table("chats").select("*").eq("meeting_id", meeting_id).order("created_at", desc=True).limit(10).execute()
    chat_history = list(reversed(history_response.data))

    # --- 6. Construct the prompt ---
    chat_history_text = "\n".join([f"{c['sender'].upper()}: {c['message']}" for c in chat_history])
    relevant_context_text = "\n---\n".join(relevant_context)
    prompt = f"""You are a helpful meeting assistant. Answer the user's question based ONLY on the provided context below.
    The context includes recent chat history and relevant sections of the meeting transcript. If the answer is not in the context, say so.

    **Chat History:**
    {chat_history_text}

    **Relevant Transcript Sections:**
    {relevant_context_text}

    **User's New Question:**
    {user_query}

    **Your Answer:**
    """
    
    # --- 7. Generate the final answer with RETRY LOGIC ---
    ai_response = None
    last_error_generation = None

    for key in api_keys:
        try:
            print(f"Attempting to generate response with a new API key...")
            genai.configure(api_key=key)
            model = genai.GenerativeModel(generative_model)
            ai_response = await model.generate_content_async(prompt)
            print(f"Response generated successfully with key ending in '...{key[-4:]}'.")
            break
        except (google.api_core.exceptions.PermissionDenied, google.api_core.exceptions.ResourceExhausted) as e:
            print(f"API key ending in '...{key[-4:]}' failed for generation. Reason: {type(e).__name__}. Trying next key...")
            last_error_generation = e
            continue

    if ai_response is None:
        raise Exception(f"All API keys failed for generation. Last error: {last_error_generation}") from last_error_generation
    
    ai_message = ai_response.text.strip()

    # --- NEW: Save the AI's response to the chat history table
    try:
        supabase.table("chats").insert({
            "meeting_id": meeting_id,
            "sender": "ai",
            "message": ai_message
        }).execute()
        print(f"AI response saved for meeting {meeting_id}.")
    except Exception as e:
        print(f"Failed to save AI response to chat history: {e}")

    return ai_message