import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()
AUTH_KEY = os.getenv("RESPONSE_KEY")
WORKER_URL = "https://tamuspe-userkey.llamas09-mango4089.workers.dev/"
headers = {'Auth-Key': AUTH_KEY}


def get():
    try:
        response = requests.get(WORKER_URL, headers=headers)

        if response.status_code == 200:
            # Assuming the response contains the file content
            key = response.content.decode('utf-8')
            return key

        else:
            print(f"Failed to retrieve key. Status code: {response.status_code}")
            return 'error'

    except:
        return 'error'
    