"""
logger.py
"""

import datetime
import json
import os
from collections import deque

from app_paths import data_dir

LOG_FILE = os.path.join(data_dir(), "trap_activity_log.json")


class TrapLogger:
    def __init__(self, max_entries=200):
        self.entries = deque(maxlen=max_entries)

    def log(self, actor, action, target, risk_level="INFO"):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "actor": actor,
            "action": action,
            "target": target,
            "risk_level": risk_level,
        }
        self.entries.append(entry)
        self._print_live(entry)

    def _print_live(self, entry):
        colors = {
            "INFO": "\033[94m",
            "SUSPICIOUS": "\033[93m",
            "TRAPPED": "\033[91m",
            "RESET": "\033[0m",
        }
        color = colors.get(entry["risk_level"], colors["RESET"])
        try:
            print(f"{color}[{entry['timestamp']}] ({entry['risk_level']}) "
                  f"{entry['actor']} → {entry['action']} → {entry['target']}{colors['RESET']}")
        except Exception:
            pass  # windowed .exe has no console; never let printing break the app

    def get_entries(self):
        return list(reversed(self.entries))

    def clear(self):
        self.entries.clear()

    def save(self):
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self.entries), f, indent=2)
        except OSError:
            pass
