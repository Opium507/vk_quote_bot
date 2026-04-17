from app.domain.models import ForwardedMessage

def _normalize_text(value: str | None) -> str:
    return (value or "").strip()

def _normalize_author_id(value) -> int | None:
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def _extract_attachment_type(attachments: list) -> str | None:
    """Возвращает строковое описание первого вложения, если оно есть."""
    if not attachments:
        return None
    attachment = attachments[0]
    att_type = attachment.get("type")
    if att_type == "photo":
        return "[Фото]"
    elif att_type == "video":
        return "[Видео]"
    elif att_type == "audio":
        return "[Аудио]"
    elif att_type == "doc":
        return "[Документ]"
    elif att_type == "sticker":
        return "[Стикер]"
    elif att_type == "wall":
        return "[Запись на стене]"
    elif att_type == "link":
        return "[Ссылка]"
    elif att_type == "graffiti":
        return "[Граффити]"
    elif att_type == "poll":
        return "[Опрос]"
    else:
        return f"[{att_type.capitalize()}]"

def _extract_text_or_placeholder(message: dict) -> str:
    """Извлекает текст сообщения или создаёт плейсхолдер из вложений."""
    text = _normalize_text(message.get("text"))
    if text:
        return text
    attachments = message.get("attachments") or []
    placeholder = _extract_attachment_type(attachments)
    if placeholder:
        return placeholder
    return "[Пустое сообщение]"

def extract_single_forward(message: dict) -> ForwardedMessage | None:
    forwards = message.get("fwd_messages") or []
    if not forwards:
        return None
    first = forwards[0]
    text = _extract_text_or_placeholder(first)
    author_id = _normalize_author_id(first.get("from_id"))
    author_name = _extract_author_name(author_id)
    return ForwardedMessage(
        text=text,
        author_name=author_name,
        author_id=author_id,
        avatar_url=None,
    )

def extract_forward_list(message: dict, limit: int = 5) -> list[ForwardedMessage]:
    forwards = (message.get("fwd_messages") or [])[:limit]
    result: list[ForwardedMessage] = []
    for item in forwards:
        text = _extract_text_or_placeholder(item)
        # даже если текст пустой, мы всё равно добавим плейсхолдер
        author_id = _normalize_author_id(item.get("from_id"))
        result.append(
            ForwardedMessage(
                text=text,
                author_name=_extract_author_name(author_id),
                author_id=author_id,
                avatar_url=None,
            )
        )
    return result

def _extract_author_name(author_id: int | None) -> str:
    if author_id is None:
        return "Неизвестный автор"
    if author_id < 0:
        return f"Сообщество {abs(author_id)}"
    return f"Пользователь {author_id}"