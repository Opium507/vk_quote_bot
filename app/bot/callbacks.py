from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CallbackAction:
    command: str
    style_key: str | None = None
    page: int | None = None


def parse_callback_payload(payload: dict[str, Any] | None) -> CallbackAction | None:
    if not payload or not isinstance(payload, dict):
        return None

    command = str(payload.get("cmd", "")).strip()
    if not command:
        return None

    style_key_raw = payload.get("style_key")
    style_key = str(style_key_raw).strip() if style_key_raw is not None else None

    page_raw = payload.get("page")
    page: int | None = None
    if page_raw is not None:
        try:
            page = int(page_raw)
        except (TypeError, ValueError):
            page = None

    return CallbackAction(
        command=command,
        style_key=style_key,
        page=page,
    )
