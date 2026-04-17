def build_style_menu_text(page: int, total_pages: int) -> str:
    return (
        "Выбери стиль для генерации одиночной цитаты.\n"
        f"Страница {page} из {total_pages}."
    )

def build_style_selected_text(style_name: str) -> str:
    return f"Выбран стиль: {style_name}."

def build_unknown_style_text() -> str:
    return "Не удалось определить стиль. Попробуй выбрать его заново."

def build_help_text() -> str:
    return (
        "Доступные команды:\n"
        "• !стиль — выбрать оформление через кнопки\n"
        "• !цитата — сделать карточку из первого пересланного сообщения\n"
        "• !цитата все — сделать карточку из всех пересланных сообщений первого слоя "
        "(до 5 штук)\n"
        "• !помощь — вызвать это сообщение"
    )

def build_missing_forward_text() -> str:
    return (
        "Нужно переслать сообщение боту.\n"
        "Для одной цитаты используй: !цитата\n"
        "Для нескольких сообщений используй: !цитата все"
    )

def build_empty_forward_text() -> str:
    return "В пересланных сообщениях не нашлось текста для карточки."

def build_too_many_forwards_text(max_count: int) -> str:
    return f"Можно обработать не больше {max_count} пересланных сообщений за раз."

def build_render_error_text() -> str:
    return "Не получилось собрать карточку. Попробуй еще раз."
