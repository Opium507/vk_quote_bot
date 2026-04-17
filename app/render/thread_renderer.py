from pathlib import Path
from uuid import uuid4
import json

from PIL import Image, ImageDraw, ImageFont

from app.domain.models import QuoteRenderRequest
from app.render.avatar_utils import load_circle_avatar
from app.render.text_utils import (
    wrap_text,
    draw_multiline_text_with_local_emoji,
)
from app.render.font_utils import load_font

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Загружаем конфиг стиля для треда
THREAD_STYLE_FILE = Path(__file__).parent / "themes" / "thread_style.json"

def _load_thread_style():
    with open(THREAD_STYLE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

THREAD_STYLE = _load_thread_style()

# Распаковываем для удобства
BG_COLOR = tuple(THREAD_STYLE["background_color"])
TITLE_COLOR = tuple(THREAD_STYLE["title_color"])
NAME_COLOR = tuple(THREAD_STYLE["name_color"])
TEXT_COLOR = tuple(THREAD_STYLE["text_color"])
BUBBLE_COLOR = tuple(THREAD_STYLE["bubble_color"])
PLACEHOLDER_AVATAR_FILL = tuple(THREAD_STYLE["placeholder_avatar_fill"])

TITLE_FONT_PATH = THREAD_STYLE["title_font"]
BODY_FONT_PATH = THREAD_STYLE["body_font"]
AUTHOR_FONT_PATH = THREAD_STYLE["author_font"]

TITLE_FONT_SIZE = THREAD_STYLE["title_font_size"]
BODY_FONT_SIZE = THREAD_STYLE["body_font_size"]
AUTHOR_FONT_SIZE = THREAD_STYLE["author_font_size"]

LINE_SPACING = THREAD_STYLE["line_spacing"]
MAX_TEXT_WIDTH = THREAD_STYLE["max_text_width"]
AVATAR_SIZE = THREAD_STYLE["avatar_size"]
BLOCK_RADIUS = THREAD_STYLE["block_radius"]
INNER_PADDING = THREAD_STYLE["inner_padding"]
AUTHOR_GAP = THREAD_STYLE["author_gap"]
BLOCK_GAP = THREAD_STYLE["block_gap"]
TITLE_Y = THREAD_STYLE["title_y"]
CONTENT_Y = THREAD_STYLE["content_y"]
BOTTOM_PADDING = THREAD_STYLE["bottom_padding"]
LEFT_MARGIN = THREAD_STYLE["left_margin"]
AVATAR_X_OFFSET = THREAD_STYLE["avatar_x_offset"]
AVATAR_Y_OFFSET = THREAD_STYLE["avatar_y_offset"]


def render_thread_quote(request: QuoteRenderRequest) -> Path:
    # Загружаем шрифты
    title_font = load_font(TITLE_FONT_PATH, TITLE_FONT_SIZE)
    body_font = load_font(BODY_FONT_PATH, BODY_FONT_SIZE)
    author_font = load_font(AUTHOR_FONT_PATH, AUTHOR_FONT_SIZE)

    measure_image = Image.new("RGB", (request.width, 10), BG_COLOR)
    measure_draw = ImageDraw.Draw(measure_image)

    message_blocks: list[dict] = []
    current_y = CONTENT_Y

    for index, message in enumerate(request.messages):
        author_text = message.author_name
        prev_message = request.messages[index - 1] if index > 0 else None
        is_new_author = prev_message is None or prev_message.author_id != message.author_id

        wrapped_lines = wrap_text(
            draw=measure_draw,
            text=message.text,
            font=body_font,
            max_width=MAX_TEXT_WIDTH,
        )
        text_block = "\n".join(wrapped_lines)
        line_widths = [
            measure_draw.textlength(line, font=body_font)
            for line in wrapped_lines
        ]
        text_max_width = max(line_widths) if line_widths else 0

        author_bbox = measure_draw.textbbox((0, 0), author_text, font=author_font)
        author_height = author_bbox[3] - author_bbox[1]

        text_bbox = measure_draw.multiline_textbbox(
            (0, 0),
            text_block,
            font=body_font,
            spacing=LINE_SPACING,
        )
        text_height = text_bbox[3] - text_bbox[1]

        if is_new_author:
            block_height = INNER_PADDING + author_height + AUTHOR_GAP + text_height + INNER_PADDING
        else:
            block_height = max(78, 16 + text_height + 16)

        if is_new_author:
            block_width = min(900, max(360, int(text_max_width) + 52))
        else:
            block_width = min(900, max(360, int(text_max_width) + 64))

        message_blocks.append(
            {
                "author_id": message.author_id,
                "author_text": author_text,
                "text_block": text_block,
                "avatar_url": message.avatar_url,
                "is_new_author": is_new_author,
                "y": current_y,
                "height": block_height,
                "width": block_width,
            }
        )
        current_y += block_height + BLOCK_GAP

    final_height = max(TITLE_Y + 220, current_y + BOTTOM_PADDING - BLOCK_GAP)

    max_block_width = max((block["width"] for block in message_blocks), default=720)
    final_width = max(900, LEFT_MARGIN + max_block_width + LEFT_MARGIN)

    image = Image.new("RGB", (final_width, final_height), BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Рисуем заголовок
    draw.text(
        (final_width // 2, TITLE_Y),
        "Цитаты великих людей",
        font=title_font,
        fill=TITLE_COLOR,
        anchor="ma",
    )

    for block in message_blocks:
        is_new_author = block["is_new_author"]

        block_x1 = LEFT_MARGIN
        block_y1 = block["y"]
        block_x2 = block_x1 + block["width"]
        block_y2 = block_y1 + block["height"]

        draw.rounded_rectangle(
            (block_x1, block_y1, block_x2, block_y2),
            radius=BLOCK_RADIUS,
            fill=BUBBLE_COLOR,
        )

        if is_new_author:
            avatar_x1 = AVATAR_X_OFFSET
            avatar_y1 = block_y1 + AVATAR_Y_OFFSET
            avatar_x2 = avatar_x1 + AVATAR_SIZE
            avatar_y2 = avatar_y1 + AVATAR_SIZE

            avatar_image = load_circle_avatar(
                avatar_url=block.get("avatar_url"),
                size=AVATAR_SIZE,
            )

            if avatar_image is not None:
                image.paste(avatar_image, (avatar_x1, avatar_y1), avatar_image)
            else:
                draw.ellipse(
                    (avatar_x1, avatar_y1, avatar_x2, avatar_y2),
                    fill=PLACEHOLDER_AVATAR_FILL,
                )
                avatar_font = ImageFont.load_default()
                draw.text(
                    ((avatar_x1 + avatar_x2) // 2, (avatar_y1 + avatar_y2) // 2),
                    ">_",
                    font=avatar_font,
                    fill=TEXT_COLOR,
                    anchor="mm",
                )

        author_x = block_x1 + INNER_PADDING
        author_y = block_y1 + 18
        if is_new_author:
            draw.text(
                (author_x, author_y),
                block["author_text"],
                font=author_font,
                fill=NAME_COLOR,
            )
            text_y = author_y + 34
        else:
            text_y = block_y1 + 18

        text_x = author_x

        draw_multiline_text_with_local_emoji(
            image=image,
            position=(text_x, text_y),
            text=block["text_block"],
            font=body_font,
            fill=TEXT_COLOR,
            spacing=LINE_SPACING,
        )

    file_path = OUTPUT_DIR / f"thread-{uuid4().hex}.png"
    image.save(file_path)
    return file_path