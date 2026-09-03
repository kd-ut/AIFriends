import os

import requests


def delete_voice(voice_id):
    headers = {
        'Authorization': f"Bearer {os.getenv('API_KEY')}",
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'voice-enrollment',
        'input': {'action': 'delete_voice', 'voice_id': voice_id},
    }
    response = requests.post(os.getenv('VOICE_URL'), headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()
