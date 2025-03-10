import requests

# Replace these values with your actual server and authentication details
WORKER_URL = "https://tamuspe-feedback.llamas09-mango4089.workers.dev/"


def send(filename, auth):
    with open(filename, 'rb') as file:
        file_content = file.read()

    url = WORKER_URL + filename
    headers = {'Auth-Key': auth}

    response = requests.put(url, headers=headers, data=file_content)

    if response.status_code == 200:
        print(f"File {filename} uploaded successfully!")
        return 'sent!'
    else:
        print(f"Failed to upload file {filename}. Status code: {response.status_code}")
        print(response.text)
        return 'error'

