import json
from functools import lru_cache
from pathlib import Path

from app.domain.models import QuoteTheme


THEMES_FILE = Path(__file__).parent / "themes" / "styles.json"


def _to_rgb(value: list[int]) -> tuple[int, int, int]:
    return tuple(value[:3])


def _build_theme(key: str, raw: dict) -> QuoteTheme:
    return QuoteTheme(
        key=raw["key"],
        display_name=raw["display_name"],
        title=raw["title"],
        background_color=_to_rgb(raw["background_color"]),
        canvas_color=_to_rgb(raw["canvas_color"]),
        text_color=_to_rgb(raw["text_color"]),
        muted_text_color=_to_rgb(raw["muted_text_color"]),
        accent_color=_to_rgb(raw["accent_color"]),
        bubble_color=_to_rgb(raw["bubble_color"]),
        bubble_text_color=_to_rgb(raw["bubble_text_color"]),
        name_color=_to_rgb(raw["name_color"]),
        separator_color=_to_rgb(raw["separator_color"]),
        title_font=raw["title_font"],
        body_font=raw["body_font"],
        author_font=raw["author_font"],
        quote_prefix=raw["quote_prefix"],
        quote_suffix=raw["quote_suffix"],
        author_prefix=raw["author_prefix"],
        author_suffix=raw.get("author_suffix", ""),
        title_font_size=raw.get("title_font_size", 56),
        body_font_size=raw.get("body_font_size", 64),
        author_font_size=raw.get("author_font_size", 42),
        max_text_width=raw.get("max_text_width", 940),
        line_spacing=raw.get("line_spacing", 16),
    )


@lru_cache(maxsize=1)
def load_all_themes() -> dict[str, QuoteTheme]:
    raw_data = json.loads(THEMES_FILE.read_text(encoding="utf-8"))
    return {
        key: _build_theme(key, theme_data)
        for key, theme_data in raw_data.items()
    }


def get_theme(theme_key: str, fallback_key: str = "classic") -> QuoteTheme:
    themes = load_all_themes()
    return themes.get(theme_key, themes[fallback_key])


def get_theme_keys() -> list[str]:
    return list(load_all_themes().keys())
