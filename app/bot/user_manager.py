import json
from pathlib import Path
from threading import Lock
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
ALLOWED_USERS_FILE = BASE_DIR / "data" / "allowed_users.json"

class UserManager:
    def __init__(self, superadmin_id: int):
        self.superadmin_id = superadmin_id
        self._lock = Lock()
        self._users: List[Dict] = []          # каждый элемент: {"id": int, "name": str, "render_count": int}
        self._superadmin_render_count: int = 0
        self._total_renders: int = 0
        self._load()

    def _load(self):
        if ALLOWED_USERS_FILE.exists():
            with open(ALLOWED_USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._users = data.get("users", [])
                self._superadmin_render_count = data.get("superadmin_render_count", 0)
                self._total_renders = data.get("total_renders", 0)
        else:
            self._users = []
            self._superadmin_render_count = 0
            self._total_renders = 0

    def _save(self):
        with self._lock:
            ALLOWED_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ALLOWED_USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "users": self._users,
                    "superadmin_render_count": self._superadmin_render_count,
                    "total_renders": self._total_renders
                }, f, ensure_ascii=False, indent=2)

    def is_allowed(self, user_id: int) -> bool:
        if user_id == self.superadmin_id:
            return True
        return any(u["id"] == user_id for u in self._users)

    def add_user(self, user_id: int, name: str) -> bool:
        if any(u["id"] == user_id for u in self._users):
            return False
        self._users.append({"id": user_id, "name": name, "render_count": 0})
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

    def increment_render_count(self, user_id: int) -> None:
        """Увеличивает счётчик рендеров для пользователя или суперадмина."""
        with self._lock:
            if user_id == self.superadmin_id:
                self._superadmin_render_count += 1
            else:
                for u in self._users:
                    if u["id"] == user_id:
                        u["render_count"] = u.get("render_count", 0) + 1
                        break
            self._total_renders += 1
            self._save()

    def get_total_renders(self) -> int:
        return self._total_renders

    def get_superadmin_render_count(self) -> int:
        return self._superadmin_render_count

    def get_user_render_count(self, user_id: int) -> int:
        if user_id == self.superadmin_id:
            return self._superadmin_render_count
        for u in self._users:
            if u["id"] == user_id:
                return u.get("render_count", 0)
        return 0