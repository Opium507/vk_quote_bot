from math import ceil

from app.bot.keyboards import build_style_menu_keyboard, build_style_selected_keyboard
from app.bot.messages import (
    build_style_menu_text,
    build_style_selected_text,
    build_unknown_style_text,
)
from app.bot.state import UserStateStore
from app.render.theme_loader import get_theme, load_all_themes


STYLES_PER_PAGE = 4


class StyleService:
    def __init__(self, state_store: UserStateStore) -> None:
        self._state_store = state_store

    def _get_themes(self):
        return list(load_all_themes().values())

    def _get_total_pages(self, themes_count: int) -> int:
        return max(1, ceil(themes_count / STYLES_PER_PAGE))

    def build_style_menu_response(self, page: int = 1) -> tuple[str, str]:
        themes = self._get_themes()
        total_pages = self._get_total_pages(len(themes))

        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        text = build_style_menu_text(page=page, total_pages=total_pages)
        keyboard = build_style_menu_keyboard(themes, page=page)
        return text, keyboard

    def select_style_for_user(
        self,
        user_id: int,
        style_key: str | None,
        page: int = 1,
    ) -> tuple[str, str, str]:
        themes = self._get_themes()
        total_pages = self._get_total_pages(len(themes))

        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        if not style_key:
            text = build_unknown_style_text()
            keyboard = build_style_selected_keyboard(page=page)
            return text, keyboard, "Стиль не определен"

        theme = get_theme(style_key)
        self._state_store.set_style(user_id, theme.key)

        text = build_style_selected_text(theme.display_name)
        keyboard = build_style_selected_keyboard(page=page)
        snackbar_text = f"Стиль: {theme.display_name}"
        return text, keyboard, snackbar_text

    def paginate_styles(self, current_page: int, direction: str) -> tuple[str, str, str]:
        themes = self._get_themes()
        total_pages = self._get_total_pages(len(themes))

        if current_page < 1:
            current_page = 1
        if current_page > total_pages:
            current_page = total_pages

        if direction == "prev":
            if current_page <= 1:
                text = build_style_menu_text(page=1, total_pages=total_pages)
                keyboard = build_style_menu_keyboard(themes, page=1)
                return text, keyboard, "Это первая страница"

            new_page = current_page - 1
            text = build_style_menu_text(page=new_page, total_pages=total_pages)
            keyboard = build_style_menu_keyboard(themes, page=new_page)
            return text, keyboard, f"Страница {new_page} из {total_pages}"

        if direction == "next":
            if current_page >= total_pages:
                text = build_style_menu_text(page=total_pages, total_pages=total_pages)
                keyboard = build_style_menu_keyboard(themes, page=total_pages)
                return text, keyboard, "Стилей больше нет, новые появятся позже"

            new_page = current_page + 1
            text = build_style_menu_text(page=new_page, total_pages=total_pages)
            keyboard = build_style_menu_keyboard(themes, page=new_page)
            return text, keyboard, f"Страница {new_page} из {total_pages}"

        text = build_style_menu_text(page=current_page, total_pages=total_pages)
        keyboard = build_style_menu_keyboard(themes, page=current_page)
        return text, keyboard, "Неизвестная команда"

    def get_stub_response(self, page: int = 1) -> tuple[str, str, str]:
        themes = self._get_themes()
        total_pages = self._get_total_pages(len(themes))

        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        text = build_style_menu_text(page=page, total_pages=total_pages)
        keyboard = build_style_menu_keyboard(themes, page=page)
        return text, keyboard, "Стиль в разработке, появится позже"

    def get_user_style_key(self, user_id: int) -> str:
        return self._state_store.get_style(user_id)
