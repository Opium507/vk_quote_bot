from math import ceil

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from app.domain.models import QuoteTheme

STYLES_PER_PAGE = 4

def build_style_menu_keyboard(themes: list[QuoteTheme], page: int = 1) -> str:
    keyboard = VkKeyboard(inline=True)

    total_styles = len(themes)
    total_pages = max(1, ceil(total_styles / STYLES_PER_PAGE))

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * STYLES_PER_PAGE
    end = start + STYLES_PER_PAGE
    page_themes = themes[start:end]

    while len(page_themes) < STYLES_PER_PAGE:
        page_themes.append(None)

    for index, theme in enumerate(page_themes, start=1):
        if theme is None:
            keyboard.add_callback_button(
                label="Скоро",
                color=VkKeyboardColor.SECONDARY,
                payload={
                    "cmd": "style_stub",
                    "page": page,
                },
            )
        else:
            keyboard.add_callback_button(
                label=theme.display_name,
                color=VkKeyboardColor.SECONDARY,
                payload={
                    "cmd": "style_select",
                    "style_key": theme.key,
                    "page": page,
                },
            )

        if index % 2 == 0 and index != len(page_themes):
            keyboard.add_line()

    keyboard.add_line()
    keyboard.add_callback_button(
        label="← Назад",
        color=VkKeyboardColor.PRIMARY,
        payload={
            "cmd": "style_page_prev",
            "page": page,
        },
    )
    keyboard.add_callback_button(
        label="Вперед →",
        color=VkKeyboardColor.PRIMARY,
        payload={
            "cmd": "style_page_next",
            "page": page,
        },
    )

    return keyboard.get_keyboard()

def build_style_selected_keyboard(page: int = 1) -> str:
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button(
        label="Вернуться",
        color=VkKeyboardColor.PRIMARY,
        payload={
            "cmd": "style_menu",
            "page": page,
        },
    )
    return keyboard.get_keyboard()
