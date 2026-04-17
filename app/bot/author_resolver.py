from app.domain.models import ForwardedMessage
from app.bot.vk_client import VkBotClient


class AuthorResolver:
    def __init__(self, vk_client: VkBotClient) -> None:
        self._vk_client = vk_client
        self._name_cache: dict[int, str] = {}
        self._avatar_cache: dict[int, str | None] = {}


    def enrich_message(self, message: ForwardedMessage) -> ForwardedMessage:
        if message.author_id is None:
            return message

        resolved_name = self._resolve_name(message.author_id)
        resolved_avatar = self._resolve_avatar_url(message.author_id)

        return ForwardedMessage(
            text=message.text,
            author_name=resolved_name,
            author_id=message.author_id,
            avatar_url=resolved_avatar,
        )

    def enrich_messages(self, messages: list[ForwardedMessage]) -> list[ForwardedMessage]:
        return [self.enrich_message(message) for message in messages]

    def _resolve_name(self, author_id: int) -> str:
        cached_name = self._name_cache.get(author_id)
        if cached_name:
            return cached_name

        if author_id < 0:
            resolved_name = self._resolve_group_name(abs(author_id))
        else:
            resolved_name = self._resolve_user_name(author_id)

        self._name_cache[author_id] = resolved_name
        return resolved_name

    def _resolve_avatar_url(self, author_id: int) -> str | None:
        if author_id in self._avatar_cache:
            return self._avatar_cache[author_id]

        if author_id < 0:
            avatar_url = self._resolve_group_avatar(abs(author_id))
        else:
            avatar_url = self._resolve_user_avatar(author_id)

        self._avatar_cache[author_id] = avatar_url
        return avatar_url


    def _resolve_user_name(self, user_id: int) -> str:
        try:
            response = self._vk_client.api.users.get(
                user_ids=user_id,
                fields="photo_100",
            )
            if not response:
                return f"Пользователь {user_id}"

            user = response[0]
            first_name = str(user.get("first_name", "")).strip()
            last_name = str(user.get("last_name", "")).strip()
            full_name = f"{first_name} {last_name}".strip()

            return full_name or f"Пользователь {user_id}"
        except Exception:
            return f"Пользователь {user_id}"

    def _resolve_user_avatar(self, user_id: int) -> str | None:
        try:
            response = self._vk_client.api.users.get(
                user_ids=user_id,
                fields="photo_100",
            )
            if not response:
                return None

            user = response[0]
            avatar_url = user.get("photo_100")
            if isinstance(avatar_url, str) and avatar_url.strip():
                return avatar_url.strip()

            return None
        except Exception:
            return None

    def _resolve_group_name(self, group_id: int) -> str:
        try:
            response = self._vk_client.api.groups.getById(group_id=group_id)
            if not response:
                return f"Сообщество {group_id}"

            group = response[0]
            group_name = str(group.get("name", "")).strip()

            return group_name or f"Сообщество {group_id}"
        except Exception:
            return f"Сообщество {group_id}"

    def _resolve_group_avatar(self, group_id: int) -> str | None:
        try:
            response = self._vk_client.api.groups.getById(group_id=group_id)
            if not response:
                return None

            group = response[0]
            avatar_url = (
                group.get("photo_100")
                or group.get("photo_50")
                or group.get("photo_200")
            )

            if isinstance(avatar_url, str) and avatar_url.strip():
                return avatar_url.strip()

            return None
        except Exception:
            return None
