import json
import os
from datetime import datetime
from typing import List, Dict

class HistoryManager:
    def __init__(self, history_file: str):
        self.history_file = os.path.expanduser(history_file)
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)

    def load_history(self) -> List[Dict]:
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def save_conversation(self, message: str, response: str) -> None:
        history = self.load_history()
        history.append({
            'timestamp': datetime.now().strftime("%I:%M %p · %b %d, %Y"),
            'message': message,
            'response': response
        })
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def clear_history(self) -> None:
        with open(self.history_file, 'w') as f:
            json.dump([], f)
