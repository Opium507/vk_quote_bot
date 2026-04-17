from threading import Lock

class UserStateStore:
    def __init__(self, default_style: str = "classic") -> None:
        self._default_style = default_style
        self._styles_by_user_id: dict[int, str] = {}
        self._lock = Lock()

    def get_style(self, user_id: int) -> str:
        with self._lock:
            return self._styles_by_user_id.get(user_id, self._default_style)

    def set_style(self, user_id: int, style_key: str) -> None:
        with self._lock:
            self._styles_by_user_id[user_id] = style_key

    def reset_style(self, user_id: int) -> None:
        with self._lock:
            self._styles_by_user_id.pop(user_id, None)
