import requests
import json
import os

def SendMessageWhatsapp(data):
    try:
        token = os.getenv("WHATSAPP_TOKEN")
        phone_id = os.getenv("PHONE_NUMBER_ID")
        api_url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
        headers = {"content-type": "application/json", "authorization": "Bearer " + token}
        response = requests.post(api_url, data=json.dumps(data), headers=headers)
        
        if response.status_code == 200:
            return True
        return False
    except Exception as exception:
        print(exception)
        return False