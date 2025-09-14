# from pydub import AudioSegment
import os
import time
import requests
from typing import List, Optional

# def convert_mp4_to_wav(mp4_file_path, output_dir):
#     # Ensure the output directory exists
#     os.makedirs(output_dir, exist_ok=True)

#     # Define the output WAV file path
#     wav_file_name = os.path.splitext(os.path.basename(mp4_file_path))[0] + '.wav'
#     wav_file_path = os.path.join(output_dir, wav_file_name)

#     # Load the MP4 file
#     audio = AudioSegment.from_file(mp4_file_path, format='mp4')

#     # Export as WAV
#     audio.export(wav_file_path, format='wav')
#     print(f"Converted {mp4_file_path} to {wav_file_path}")

#     return wav_file_path



def check_file_status(file_uri, api_key, max_retries=10, wait_time=5):
    status_url = file_uri  # The file URI can be used to check its status
    headers = {
        "x-goog-api-key": api_key
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(status_url, headers=headers, verify=False)  # Set verify=True in production
            response.raise_for_status()  # Raise an error for bad responses

            file_info = response.json()
            state = file_info.get('state')
            print(f"Current file state: {state}")

            if state == 'ACTIVE':
                return True
            elif state in ['FAILED', 'EXPIRED']:
                print(f"File processing failed or expired: {state}")
                return False

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Log HTTP errors
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")  # Log other request errors
        except Exception as e:
            print(f"An unexpected error occurred: {e}")  # Log unexpected errors

        # Wait before checking again
        print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
        time.sleep(wait_time)

    print("Max retries reached. File status could not be determined.")
    return False





def create_embeddings(supabase, text, meeting_id):
    try:
        response = supabase.rpc("create_embedding", {"input_text": text}).execute()
        if response.error:
            print(f"Error creating embedding: {response.error.message}")
            return None
        embedding = response.data[0]['embedding']
        print(f"Embedding created for meeting {meeting_id}")
        return embedding
    except Exception as e:
        print(f"Exception during embedding creation: {e}")
        return None
    




# In main.py, before your API endpoints

async def enrich_participants(supabase, host, participant_emails: List[str]) -> List[dict]:
    """
    Takes a list of emails, fetches corresponding names from the 'profiles' table,
    and returns a list of participant objects with names and emails.
    Provides a fallback name if a profile is not found.
    """
    if not participant_emails:
        return []

    # 1. Fetch all matching profiles in a single, efficient query
    profiles_response = supabase.table("profiles").select("email, firstName, lastName").in_("email", participant_emails).execute()

    # 2. Create a lookup map for easy access (email -> full name)
    profiles_map = {
        profile['email']: f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
        for profile in profiles_response.data
    }

    # 3. Build the final list of participant objects
    enriched_list = []
    for email in participant_emails:
        # Use the fetched name, or create a fallback if not found
        name = profiles_map.get(email)
        if not name:
            # Fallback: use the part of the email before the '@'
            name = email.split('@')[0].replace('.', ' ').title()

        enriched_list.append({
            "email": email,
            "name": name,
            "role": "Participant" if email != host else "Host"
        })
        
    return enriched_list