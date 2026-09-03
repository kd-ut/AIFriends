import os

import requests


def list_voice():
    headers = {
        'Authorization': f"Bearer {os.getenv('API_KEY')}",
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'voice-enrollment',
        'input': {'action': 'list_voice', 'page_size': 100, 'page_index': 0},
    }
    response = requests.post(os.getenv('VOICE_URL'), headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()
