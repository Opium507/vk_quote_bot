from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class RenderMode(StrEnum):
    SINGLE = "single"
    THREAD = "thread"


@dataclass(frozen=True)
class QuoteTheme:
    key: str
    display_name: str
    title: str
    background_color: tuple[int, int, int]
    canvas_color: tuple[int, int, int]
    text_color: tuple[int, int, int]
    muted_text_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    bubble_color: tuple[int, int, int]
    bubble_text_color: tuple[int, int, int]
    name_color: tuple[int, int, int]
    separator_color: tuple[int, int, int]
    title_font: str
    body_font: str
    author_font: str
    quote_prefix: str
    quote_suffix: str
    author_prefix: str
    author_suffix: str = ""
    title_font_size: int = 56
    body_font_size: int = 64
    author_font_size: int = 42
    max_text_width: int = 940
    line_spacing: int = 16


@dataclass(frozen=True)
class ForwardedMessage:
    text: str
    author_name: str
    author_id: int | None = None
    avatar_url: Optional[str] = None


@dataclass(frozen=True)
class QuoteRenderRequest:
    mode: RenderMode
    theme: QuoteTheme
    messages: list[ForwardedMessage] = field(default_factory=list)
    width: int = 1080
    height: int = 1080
