import requests

WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
ACCESS_TOKEN = "EAAIZCTzaF1osBPlFn8V13lWJgsFjTh4twQZC7MMT0WcOhwL1q3FcD5NcRvZBGu6AWx0ve5t8ZB6ZB4UTc7ZBYbngqSwkZB63ouRuxk8TUE451SqMCZB3IneBuNtfNhAtUPy0WrT2YrGq54Rm0eFaWMQBPXUmgzEKfUvdCZA0MtEtY2i4ubzdAetsFbtsa1NM1MZBkhPwZDZD"
PHONE_NUMBER_ID = "810808242121215"
TO_NUMBER = "61432154351"

url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "messaging_product": "whatsapp",
    "to": TO_NUMBER,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {"code": "en_US"}
    }
}

print("[SENDING] Template message to WhatsApp...")
response = requests.post(url, headers=headers, json=data)
print(f"[STATUS] {response.status_code}")
print(f"[RESPONSE] {response.text}")

if response.status_code == 200:
    print("[SUCCESS] Message sent to your WhatsApp!")
else:
    print("[ERROR] Failed to send")
