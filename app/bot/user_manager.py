import json
from pathlib import Path
from threading import Lock
from typing import List, Dict, Optional

# Определяем путь относительно этого файла
BASE_DIR = Path(__file__).parent.parent  # поднимаемся из app/bot в app/
ALLOWED_USERS_FILE = BASE_DIR / "data" / "allowed_users.json"


class UserManager:
    def __init__(self, superadmin_id: int):
        self.superadmin_id = superadmin_id
        self._lock = Lock()
        self._users: List[Dict] = []
        self._load()

    def _load(self):
        if ALLOWED_USERS_FILE.exists():
            with open(ALLOWED_USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._users = data.get("users", [])
        else:
            self._users = []

    def _save(self):
        with self._lock:
            # Создаём папку data, если её нет
            ALLOWED_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ALLOWED_USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({"users": self._users}, f, ensure_ascii=False, indent=2)

    def is_allowed(self, user_id: int) -> bool:
        if user_id == self.superadmin_id:
            return True
        return any(u["id"] == user_id for u in self._users)

    def add_user(self, user_id: int, name: str) -> bool:
        if any(u["id"] == user_id for u in self._users):
            return False
        self._users.append({"id": user_id, "name": name})
        self._save()
        return True

    def remove_user(self, user_id: int) -> bool:
        original_len = len(self._users)
        self._users = [u for u in self._users if u["id"] != user_id]
        if len(self._users) < original_len:
            self._save()
            return True
        return False

    def list_users(self) -> List[Dict]:
        return self._users.copy()

    def get_user_name(self, user_id: int) -> Optional[str]:
        for u in self._users:
            if u["id"] == user_id:
                return u["name"]
        return None