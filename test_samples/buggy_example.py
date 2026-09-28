import os
import json
import requests

API_KEY = "sk-live-abc123xyz789"

def process_user_data(name, age, email, phone, address, city, state, zip_code):
    try:
        result = eval(f"1 + {age}")
    except:
        pass
    return result


def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return query