from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import emoji
from PIL import Image, ImageDraw, ImageFont


EMOJI_DIR = Path("app/assets/emoji")
_EMOJI_CACHE: dict[str, Image.Image] = {}


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> List[str]:
    normalized_text = (
        text.replace("\r\n", "\n")
        .replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
    )

    paragraphs = normalized_text.split("\n")
    result_lines: List[str] = []

    for paragraph in paragraphs:
        words = paragraph.split()

        if not words:
            result_lines.append("")
            continue

        current_line = words[0]

        for word in words[1:]:
            candidate = f"{current_line} {word}"
            candidate_width = draw.textlength(candidate, font=font)

            if candidate_width <= max_width:
                current_line = candidate
            else:
                result_lines.append(current_line)
                current_line = word

        result_lines.append(current_line)

    return result_lines


def draw_multiline_text_with_local_emoji(
    image: Image.Image,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    spacing: int,
) -> None:
    draw = ImageDraw.Draw(image)
    x, y = position

    lines = text.splitlines() or [""]

    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = bbox[3] - bbox[1]

    current_y = y
    for line in lines:
        _draw_text_line_with_local_emoji(
            image=image,
            draw=draw,
            position=(x, current_y),
            text=line,
            font=font,
            fill=fill,
        )
        current_y += line_height + spacing


def _emoji_to_filename(text: str) -> str:
    codepoints = "-".join(f"{ord(char):x}" for char in text)
    return f"{codepoints}.png"


def _get_emoji_path(text: str) -> Path | None:
    emoji_path = EMOJI_DIR / _emoji_to_filename(text)
    if emoji_path.exists():
        return emoji_path
    return None


def _tokenize_text_with_emoji(text: str) -> List[Tuple[str, str]]:
    tokens: List[Tuple[str, str]] = []
    last_index = 0

    for match in emoji.emoji_list(text):
        start = match["match_start"]
        end = match["match_end"]
        emoji_text = match["emoji"]

        if start > last_index:
            tokens.append(("text", text[last_index:start]))

        tokens.append(("emoji", emoji_text))
        last_index = end

    if last_index < len(text):
        tokens.append(("text", text[last_index:]))

    if not tokens:
        tokens.append(("text", text))

    return tokens


def _draw_text_line_with_local_emoji(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: Tuple[int, int, int],
) -> None:
    x, y = position
    tokens = _tokenize_text_with_emoji(text)

    if not tokens:
        draw.text((x, y), text, font=font, fill=fill)
        return

    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = bbox[3] - bbox[1]
    emoji_size = max(16, int(line_height * 0.95))

    current_x = x

    for token_type, value in tokens:
        if token_type == "text":
            if value:
                draw.text((current_x, y), value, font=font, fill=fill)
                current_x += draw.textlength(value, font=font)
            continue

        emoji_path = _get_emoji_path(value)
        if emoji_path is None:
            draw.text((current_x, y), value, font=font, fill=fill)
            current_x += draw.textlength(value, font=font)
            continue

        cache_key = str(emoji_path)
        if cache_key not in _EMOJI_CACHE:
            _EMOJI_CACHE[cache_key] = Image.open(emoji_path).convert("RGBA")

        emoji_image = _EMOJI_CACHE[cache_key].copy()
        emoji_image = emoji_image.resize((emoji_size, emoji_size), Image.LANCZOS)

        emoji_y = int(y + (line_height - emoji_size) / 2)
        image.paste(emoji_image, (int(current_x), emoji_y), emoji_image)

        current_x += emoji_size
