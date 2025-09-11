# In a file like utility.py

import json
import requests
import time
import google.generativeai as genai
from supabase import Client
import os
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer # <-- Import this
load_dotenv()

# Get API key from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

async def get_rag_response_gemini(
    supabase: Client,
    meeting_id: str,
    user_query: str,
    embedding_model: str = 'text-embedding-004',
    generative_model: str = 'gemini-1.5-flash'
) -> str:
    """
    Performs a full RAG pipeline to get a context-aware answer from a generative model.
    
    Args:
        supabase: The Supabase client.
        meeting_id: The ID of the meeting to query.
        user_query: The user's question.
        embedding_model: The model to use for creating embeddings.
        generative_model: The model to use for generating the final answer.
        
    Returns:
        The AI-generated response as a string.
    """
    match_threshold = 0.8  # Similarity threshold for filtering
    match_count = 5        # Number of top chunks to retrieve

    # --- 1. Create an embedding for the user's query ---
    query_embedding_result = genai.embed_content(
        model=embedding_model,
        content=user_query,
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=1536  # Ensure this matches your embedding model's output size
    )
    query_embedding = query_embedding_result['embedding']
    print(f"Created query embedding of length {len(query_embedding)}")
    # --- 2. Retrieve relevant context and chat history ---
    # relevant_chunks_response = supabase.rpc('match_meeting_chunks', {
    #     'query_embedding': query_embedding,
    #     'p_meeting_id': meeting_id,
    #     'match_threshold': 0.5,
    #     'match_count': 5
    # }).execute()
    # relevant_chunks = [item['content'] for item in relevant_chunks_response.data]
    print("Fetching all embedding chunks for the meeting...")
    all_chunks_response = supabase.table("meeting_embeddings").select("content, embedding").eq("meeting_id", meeting_id).execute()

    if not all_chunks_response.data:
        print("No chunks found for this meeting.")
        return "I could not find any information for this meeting."

    all_chunks = all_chunks_response.data
    print(f"Retrieved {len(all_chunks)} total chunks from the database.")


    # --- 3. Calculate similarity for each chunk in Python ---
    scored_chunks = []
    for i, chunk in enumerate(all_chunks):
        embedding_list = json.loads(chunk['embedding'])
        chunk_vector = np.array(embedding_list, dtype=np.float32)

        print(f"DEBUG: Chunk {i+1} Vector Magnitude: {np.linalg.norm(chunk_vector)}")

        # Cosine similarity for normalized vectors is just the dot product
        similarity = np.dot(query_embedding, chunk_vector)
        scored_chunks.append({
            "content": chunk['content'],
            "similarity": similarity
        })
    print(f"Calculated similarity scores for {len(scored_chunks)} chunks.")
    print("Top 5 similarity scores:")
    for item in sorted(scored_chunks, key=lambda x: x['similarity'], reverse=True)[:5]:
        print(f"  - Score: {item['similarity']:.4f}, Content Start: {item['content'][:50]}...")
    # --- 4. Filter, Sort, and Limit the chunks ---
    # Filter out chunks below the similarity threshold
    relevant_chunks_filtered = [c for c in scored_chunks if c['similarity'] >= match_threshold]

    # Sort the remaining chunks by similarity in descending order
    relevant_chunks_sorted = sorted(relevant_chunks_filtered, key=lambda x: x['similarity'], reverse=True)

    # Take the top N chunks
    top_chunks = relevant_chunks_sorted[:match_count]
    
    # Extract just the content for the final prompt
    relevant_context = [item['content'] for item in top_chunks]

    print(f"Found {len(relevant_context)} relevant chunks after filtering and sorting.")
    if relevant_context:
        # Optional: Print the top chunks and their scores for debugging
        for i, chunk in enumerate(top_chunks):
             print(f"  - Chunk {i+1} (Score: {chunk['similarity']:.4f}): {chunk['content'][:100]}...")

    # --- The rest of the function remains the same ---


# --- 5. Retrieve Chat History ---
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

    # --- 4. Generate the final answer ---
    model = genai.GenerativeModel(generative_model)
    response = await model.generate_content_async(prompt)
    
    return response.text.strip()






async def get_rag_response(
    supabase: Client,
    meeting_id: str,
    user_query: str,
    embedding_model: str = '',
    generative_model: str = 'gemini-1.5-flash'
) -> str:
    """
    Performs a full RAG pipeline to get a context-aware answer from a generative model.
    
    Args:
        supabase: The Supabase client.
        meeting_id: The ID of the meeting to query.
        user_query: The user's question.
        embedding_model: The model to use for creating embeddings.
        generative_model: The model to use for generating the final answer.
        
    Returns:
        The AI-generated response as a string.
    """
    match_threshold = 0.45  # Similarity threshold for filtering
    match_count = 5        # Number of top chunks to retrieve

    embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    
    # --- 1. Create an embedding for the user's query ---
    query_embedding = embedding_model.encode(user_query, show_progress_bar=True, normalize_embeddings=True)


    # query_embedding = query_embedding_result['embedding']
    print(f"Created query embedding of length {len(query_embedding)}")

    print("Fetching all embedding chunks for the meeting...")
    all_chunks_response = supabase.table("meeting_embeddings").select("content, embedding").eq("meeting_id", meeting_id).execute()

    if not all_chunks_response.data:
        print("No chunks found for this meeting.")
        return "I could not find any information for this meeting."

    all_chunks = all_chunks_response.data
    print(f"Retrieved {len(all_chunks)} total chunks from the database.")


    # --- 3. Calculate similarity for each chunk in Python ---
    scored_chunks = []
    for i, chunk in enumerate(all_chunks):
        embedding_list = json.loads(chunk['embedding'])
        chunk_vector = np.array(embedding_list, dtype=np.float32)

        print(f"DEBUG: Chunk {i+1} Vector Magnitude: {np.linalg.norm(chunk_vector)}")

        # Cosine similarity for normalized vectors is just the dot product
        similarity = np.dot(query_embedding, chunk_vector)
        scored_chunks.append({
            "content": chunk['content'],
            "similarity": similarity
        })
    print(f"Calculated similarity scores for {len(scored_chunks)} chunks.")
    print("Top 5 similarity scores:")
    for item in sorted(scored_chunks, key=lambda x: x['similarity'], reverse=True)[:5]:
        print(f"  - Score: {item['similarity']:.4f}, Content Start: {item['content'][:50]}...")
    # --- 4. Filter, Sort, and Limit the chunks ---
    # Filter out chunks below the similarity threshold
    relevant_chunks_filtered = [c for c in scored_chunks if c['similarity'] >= match_threshold]

    # Sort the remaining chunks by similarity in descending order
    relevant_chunks_sorted = sorted(relevant_chunks_filtered, key=lambda x: x['similarity'], reverse=True)

    # Take the top N chunks
    top_chunks = relevant_chunks_sorted[:match_count]
    
    # Extract just the content for the final prompt
    relevant_context = [item['content'] for item in top_chunks]

    print(f"Found {len(relevant_context)} relevant chunks after filtering and sorting.")
    if relevant_context:
        # Optional: Print the top chunks and their scores for debugging
        for i, chunk in enumerate(top_chunks):
             print(f"  - Chunk {i+1} (Score: {chunk['similarity']:.4f}): {chunk['content'][:100]}...")

    # --- The rest of the function remains the same ---


# --- 5. Retrieve Chat History ---
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

    # --- 4. Generate the final answer ---
    model = genai.GenerativeModel(generative_model)
    response = await model.generate_content_async(prompt)
    
    return response.text.strip()