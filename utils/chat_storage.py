import json
import os

CHAT_FILE = "data/chat_history.json"


def load_chat():
    if not os.path.exists(CHAT_FILE):
        return []
    with open(CHAT_FILE, "r") as f:
        return json.load(f)


def save_chat(messages):
    with open(CHAT_FILE, "w") as f:
        json.dump(messages, f, indent=2)


def clear_chat():
    with open(CHAT_FILE, "w") as f:
        json.dump([], f)
