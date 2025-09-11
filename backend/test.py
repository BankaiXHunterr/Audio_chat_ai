# import os
# from dotenv import load_dotenv
# from supabase import create_client, Client
# import uuid
# from modules.generate_embedding import create_and_store_embeddings_manually
# import asyncio

# # --- 1. Setup ---
# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY") # This should be your 'anon' key

# # Replace with the credentials of a test user in your project
# TEST_USER_EMAIL = "avnishmishra.ai@gmail.com"
# TEST_USER_PASSWORD = "140912"

# # Initialize the Supabase client
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# async def test_embedding_function():
#     """
#     Logs in a test user and invokes the 'create-embeddings' Edge Function.
#     """
#     try:
#         # --- 2. Authenticate as a Test User ---
#         # The client will automatically handle and use the JWT for subsequent requests.
#         print(f"Authenticating as {TEST_USER_EMAIL}...")
#         auth_response = supabase.auth.sign_in_with_password({
#             "email": TEST_USER_EMAIL,
#             "password": TEST_USER_PASSWORD
#         })
        
#         if not auth_response.session:
#             print("❌ Authentication failed. Please check your test user credentials.")
#             return

#         print("✅ Authentication successful.")

#         with open('response.txt', 'r') as f:
#             transcript_text = f.read()

#         meeting_id = "16675117-128c-4571-bbc1-456eac4c906c"
#         await create_and_store_embeddings_manually(supabase, meeting_id, transcript_text)

#         # --- 3. Prepare the Payload for the Edge Function ---
#         # test_meeting_id = str(uuid.uuid4())
#         # test_chunks = [
#         #     "This is the first text chunk for our test meeting.",
#         #     "We are discussing the project timeline and key deliverables.",
#         #     "The final topic is the budget for the next quarter."
#         # ]
        
#         # payload = {
#         #     "meeting_id": test_meeting_id,
#         #     "chunks": test_chunks
#         # }
        
#         # # --- 4. Invoke the Edge Function ---
#         # print("\nInvoking the 'create-embeddings' Edge Function...")
#         # response = supabase.functions.invoke(
#         #     function_name="create-embeddings",
#         #     invoke_options={'body': payload}
#         # )
        
#         # # --- 5. Print the Result ---
#         # print("\n✅ Edge Function executed successfully!")
#         # print("Response from function:", response)
        
#     except Exception as e:
#         print(f"\n❌ An error occurred during the test: {e}")

# # --- Run the test ---
# if __name__ == "__main__":
#     asyncio.run(test_embedding_function())




# # import json
# # import os


# # with open('response.json', 'r') as f:
# #     data = json.load(f)


# # with open('response.txt', 'w') as f:
# #     f.write("\n".join([f"{x.get('speaker')}: {x.get('text')}" for x in data]))
# # # print("\n".join([f"{x.get('speaker')}: {x.get('text')}" for x in data[:10]]))



from PIL import Image
import os

# --- Configuration ---
# 1. Put the name of your original, high-resolution image here
INPUT_IMAGE_PATH = 'logo.png' 

# 2. Define all the square icon sizes you want to generate
SIZES = [72,96,128,144,152,192,384,512]

# 3. Name of the folder where the new icons will be saved
OUTPUT_FOLDER = 'icons'
# --- End of Configuration ---


def create_resized_images():
    """
    Resizes an image to multiple specified sizes and saves them with a
    standardized filename format.
    """
    # Create the output folder if it doesn't already exist
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output directory: '{OUTPUT_FOLDER}/'")

    try:
        # Open the original image using a 'with' statement
        with Image.open(INPUT_IMAGE_PATH) as img:
            print(f"Processing '{INPUT_IMAGE_PATH}'...")
            
            # Loop through all the sizes defined in the SIZES list
            for size in SIZES:
                # Resize the image. Image.Resampling.LANCZOS is a high-quality filter
                # ideal for downscaling images like logos.
                resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # Construct the new filename, e.g., "icon-32x32.png"
                output_filename = f"icon-{size}x{size}.png"
                
                # Create the full path for saving the file
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                # Save the resized image
                resized_img.save(output_path)
                print(f"-> Saved {output_filename}")
                
            print("\nSuccessfully created all icons!")

    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{INPUT_IMAGE_PATH}'. Please check the filename.")
    except Exception as e:
        print(f"An error occurred: {e}")


# This allows the script to be run directly from the command line
if __name__ == "__main__":
    create_resized_images()