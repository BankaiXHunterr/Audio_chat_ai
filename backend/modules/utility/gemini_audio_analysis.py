import requests
import json
import base64
import os, mimetypes
from modules.upload_file_to_gemini import FileUploader
# import dotenv
from modules.prompt_tools import TOOL1
import requests
import time
from modules.utility import convert_mp4_to_wav, check_if_file_is_active
from azure.data.tables import TableServiceClient, TableEntity
import dotenv
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


dotenv.load_dotenv("/home/ipruvm/customer_support_gemini/.env")
# Azure Table Storage setup
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")  # Replace with your Azure connection string
print(f"AZURE_CONNECTION_STRING:{AZURE_CONNECTION_STRING}")
TABLE = "CSAUDIOANALYSIS"


API_KEY_GEMINI = "AIzaSyDHXuYSs3m20NdRCBnN3qpoDS75_lMTFHA"
GEMINI_FILE_UPLOAD_API_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
PROXY = {
    "http" : "http://10.238.7.4:8080",
    "https" : "http://10.238.7.4:8080",
}
gemini_file_uploader = FileUploader(upload_url=GEMINI_FILE_UPLOAD_API_URL,api_key=API_KEY_GEMINI,proxies=PROXY)




model_name = "gemini-2.5-flash-lite"
# api_end_point = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
api_end_point = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

table_service_client = TableServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
table_client = table_service_client.get_table_client(TABLE)

        # entity = table_client.get_entity(partition_key='user',row_key=email)



prompt = """You are an expert in analyzing the audio. Transcribe the call in the dirization format & retrun all the required parameters listed in the tool.

            Defination different type of Tone:
                
                Satisfied: The customer expresses contentment with the resolution provided and gratitude towards the support received.
                Frustrated: The customer remains upset due to unresolved issues or dissatisfaction with the service.
                Indifferent: The customer shows a lack of strong feelings or interest in the outcome of the service call.
                Relieved: The customer feels a sense of relief after a problem is resolved or a concern is adequately addressed.
                Confused: The customer is left with uncertainty or lack of understanding regarding the information or solution provided.

            Note:
            Make sure to correct the following to words if they are captured wrong while in the transcript.
            Here are few words which might be wrongly captured in the transcript so correct it while providing summary & discriptive summary.
            
            Important words:
               - ICICI Prudential Mutual Fund
               - ICICI Bank
               - Large Cap
               - PAN
               - SIP
               - Folio
               - Bluechip Fund
               - Flexi Cap
               - Large & Mid Cap
               - Multicap Fund
               - Thematic
               - Value Fund
               - ELSS
               - Focused Fund
               - Sectoral/Thematic
               - Dividend Yield
               - Mid Cap Fund
               - Small Cap Fund
               - Sectoral
               - Aggressive Hybrid
               - Arbitrage
               - Dynamic Asset Allocation/Balanced Advantage
               - Equity Savings
               - Conservative Hybrid
               - Multi Asset Allocation
               - Overnight Fund
               - Money Market Fund
               - Other Scheme (FOF)
               - Low Duration Fund
               - Floater Fund
               - Short Duration Fund
               - Medium to Long Duration Fund
               - Corporate Bond Fund
               - Banking & PSU Fund
               - Credit Risk Fund
               - Medium Duration Fund
               - Long Duration Fund
               - Dynamic Fund
               - Gilt Fund
               - Gilt Fund with 10-year Constant Duration
               - Solution oriented scheme
               - Closed Ended

               ETF:
               - ETF Funds
               - Index Schemes
               - Other Scheme (FOF)
    """

header = {
    "x-goog-api-key":API_KEY_GEMINI
}



def check_file_status(file_uri, api_key, max_retries=10, wait_time=5):
    status_url = file_uri  # The file URI can be used to check its status
    headers = {
        "x-goog-api-key": api_key
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(status_url, headers=headers, verify=False,proxies=PROXY)  # Set verify=True in production
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
# After uploading the file

md5 = "fa01fd0a31f567b3205e7c1381a32956"
zip_file_name = "20250817.zip"
part_key = "20250817"

# for item in os.listdir("/home/ipruvm/customer_support_gemini/mp4"):
#     convert_mp4_to_wav(mp4_file_path=f"/home/ipruvm/customer_support_gemini/mp4/{item}",output_dir="/home/ipruvm/customer_support_gemini/cache")



non_processed_file = []

for item in os.listdir("/home/ipruvm/customer_support_gemini/cache"):
    file_path = f"/home/ipruvm/customer_support_gemini/cache/{item}"

    print(f"File name:{item}\n\n")
    file_uri, mime_type = gemini_file_uploader.upload_file(file_path=file_path)

    if check_if_file_is_active(file_uri=file_uri,proxy=PROXY,header=header):
    

    # Construct payload for generateContent API  

    # if check_file_status(file_uri=file_uri,api_key=API_KEY_GEMINI):

        gemini_payload = {  
        "contents": [  
            {  
                "role": "user",  
                "parts": [  
                    {  
                        "fileData": {  
                            "fileUri": file_uri,  
                            "mimeType": mime_type  
                        }

                    },
                    {  
                        "text": prompt
                    } 
                ]  
            }  
        ],
        "tools":[
            {
                "function_declarations": [TOOL1]  # Ensure tool1 is defined in your context
                }
            ],
        "tool_config":{
            "function_calling_config":{"mode":"ANY"},
        }
        } 

        header = {
        "x-goog-api-key":API_KEY_GEMINI,
        "Content-Type":"application/json"}

        try:
            start = time.time()
            response = requests.post(api_end_point,headers=header,
                                        json=gemini_payload,
                                        proxies=PROXY,
                                        verify=False,
                                        timeout=600)
            
            print(response.text)
            if response.status_code == 200:
                response_dict = response.json()

                if response_dict.get("candidates")[0].get("finishReason") != "STOP":

                    with open(f"/home/ipruvm/customer_support_gemini/json_output_max_token/{item}.json",'w') as f:
                        json.dump(response_dict,f,indent=4)
                        continue
                else:   

                    if len(response_dict.get("candidates")[0].get("content").get("parts")) == 1:
                        entity = response_dict.get("candidates")[0].get("content").get("parts")[0].get("functionCall").get("args")
                    else:
                        for i in len(response_dict.get("candidates")[0].get("content").get("parts")):
                            if response_dict.get("candidates")[0].get("content").get("parts")[i].get("functionCall",None) is not None:
                                if response_dict.get("candidates")[0].get("content").get("parts")[i].get("functionCall").get("args",None) is not None: 
                                    entity = response_dict.get("candidates")[0].get("content").get("parts")[i].get("functionCall").get("args")


                meta_data = response_dict.get("usageMetadata")
                prompt_token_meta_data = {"PromptInputTokenCount":meta_data.get("promptTokenCount",0),
                                    "OutputTokenCount":meta_data.get("candidatesTokenCount",0),
                                    "TotalTokenCount":meta_data.get("totalTokenCount",0),
                                    "AudioTokenCount":[x.get("tokenCount") for x in meta_data.get("promptTokensDetails") if x.get("modality")=="AUDIO"][0]

                                    }
                
                entity["Postcall"] = ", ".join([x for x in set(entity.get("Agent Task")) - set(entity.get("Customer Task"))])
                entity["ParametersChecked"] = ", ".join(entity.get("Parameters Checked")) 
                entity["PartitionKey"] = part_key
                entity["md5"] = md5
                entity["ZipFileName"] = zip_file_name
                entity["RowKey"] = item
                entity = entity | prompt_token_meta_data

                entity = {"".join(k.split(" ")):", ".join(v) if isinstance(v,list) else v for k,v in entity.items()}
                end = time.time()
                entity["TimeTakeForProcessingRequest"] = end - start
                try:
                    table_client.create_entity(entity=entity)
                except Exception as e:
                    print(f"[line-252] got the following errro:{e}")
                with open(f"/home/ipruvm/customer_support_gemini/json_output/{item}.json",'w') as f:
                    json.dump(response_dict,f,indent=4)

            else:
                 
                non_processed_file[item] = response.text
                
                with open(f"/home/ipruvm/customer_support_gemini/json_output_not_processed/{item}.json",'w') as f:
                    json.dump({"response_text":response.text},f,indent=4)

                

        except Exception as e:
            print(e)
    print("\n")
    print("="*120)
    print("\n")
    



                                