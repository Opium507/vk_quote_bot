import json
from pathlib import Path
from typing import Any
from pathlib import Path

import vk_api
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id

import time
import requests

class VkBotClient:
    def __init__(self, token: str, group_id: int) -> None:
        self.group_id = group_id
        self.session = vk_api.VkApi(token=token)
        self.api = self.session.get_api()
        self.upload = VkUpload(self.session)

    def send_text(
        self,
        peer_id: int,
        message: str,
        keyboard: str | None = None,
    ) -> int:
        return self.api.messages.send(
            peer_id=peer_id,
            random_id=get_random_id(),
            message=message,
            keyboard=keyboard,
        )

    def edit_text(
        self,
        peer_id: int,
        conversation_message_id: int,
        message: str,
        keyboard: str | None = None,
    ) -> int:
        return self.api.messages.edit(
            peer_id=peer_id,
            conversation_message_id=conversation_message_id,
            message=message,
            keyboard=keyboard,
        )

    def send_photo(
        self,
        peer_id: int,
        image_path: str | Path,
        message: str = "",
    ) -> int:
        image_path = Path(image_path)
        last_error = None

        try:
            for attempt in range(3):
                try:
                    uploaded = self.upload.photo_messages(
                        photos=str(image_path),
                        peer_id=peer_id,
                    )[0]

                    attachment = self._build_photo_attachment(uploaded)

                    return self.api.messages.send(
                        peer_id=peer_id,
                        random_id=get_random_id(),
                        message=message,
                        attachment=attachment,
                    )

                except requests.exceptions.RequestException as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    raise

        finally:
            try:
                if image_path.exists():
                    image_path.unlink()
            except OSError:
                pass
            
    def answer_callback(
        self,
        event_id: str,
        user_id: int,
        peer_id: int,
        text: str,
    ) -> Any:
        event_data = json.dumps(
            {
                "type": "show_snackbar",
                "text": text,
            },
            ensure_ascii=False,
        )

        return self.api.messages.sendMessageEventAnswer(
            event_id=event_id,
            user_id=user_id,
            peer_id=peer_id,
            event_data=event_data,
        )

    @staticmethod
    def _build_photo_attachment(photo: dict[str, Any]) -> str:
        owner_id = photo["owner_id"]
        media_id = photo["id"]
        access_key = photo.get("access_key")

        if access_key:
            return f"photo{owner_id}_{media_id}_{access_key}"

        return f"photo{owner_id}_{media_id}"
