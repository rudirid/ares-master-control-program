"""
Quick test to send a message directly via WhatsApp Cloud API
"""

import requests
import json

# Configuration
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
ACCESS_TOKEN = "EAAIZCTzaF1osBPlFn8V13lWJgsFjTh4twQZC7MMT0WcOhwL1q3FcD5NcRvZBGu6AWx0ve5t8ZB6ZB4UTc7ZBYbngqSwkZB63ouRuxk8TUE451SqMCZB3IneBuNtfNhAtUPy0WrT2YrGq54Rm0eFaWMQBPXUmgzEKfUvdCZA0MtEtY2i4ubzdAetsFbtsa1NM1MZBkhPwZDZD"
PHONE_NUMBER_ID = "810808242121215"
TO_NUMBER = "61432154351"  # Your phone (without +)

# Message to send
message = "SUCCESS! Ares system end-to-end test complete. WhatsApp responses working!"

# API request
url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "messaging_product": "whatsapp",
    "to": TO_NUMBER,
    "type": "text",
    "text": {"body": message}
}

print("=" * 70)
print("TESTING WHATSAPP SEND")
print("=" * 70)
print(f"To: +{TO_NUMBER}")
print(f"Message: {message}")
print()

try:
    print("Sending request to WhatsApp Cloud API...")
    response = requests.post(url, headers=headers, json=data)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print()

    if response.status_code == 200:
        print("✅ SUCCESS! Message sent to WhatsApp")
        print("Check your phone!")
    else:
        print("❌ FAILED! Error from WhatsApp API")
        response.raise_for_status()

except Exception as e:
    print(f"❌ EXCEPTION: {e}")
