from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont

from app.domain.models import QuoteRenderRequest
from app.render.avatar_utils import load_circle_avatar
from app.render.text_utils import (
    wrap_text,
    draw_multiline_text_with_local_emoji,
)
from app.render.font_utils import load_font   # <-- новый импорт

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
EMOJI_DIR = Path("app/assets/emoji")


def render_single_quote(request: QuoteRenderRequest) -> Path:
    theme = request.theme
    message = request.messages[0]

    title_font = load_font(theme.title_font, theme.title_font_size)
    quote_font = load_font(theme.body_font, theme.body_font_size)
    author_font = load_font(theme.author_font, theme.author_font_size)

    quote_text = f"{theme.quote_prefix}{message.text}{theme.quote_suffix}"
    quote_lines = wrap_text(
        draw=ImageDraw.Draw(Image.new("RGB", (request.width, 10), theme.canvas_color)),
        text=quote_text,
        font=quote_font,
        max_width=theme.max_text_width,
    )
    
    quote_block = "\n".join(quote_lines)

    quote_bbox = ImageDraw.Draw(Image.new("RGB", (request.width, 10), theme.canvas_color)).multiline_textbbox(
        (70, 240),
        quote_block,
        font=quote_font,
        spacing=theme.line_spacing,
    )
    quote_height = quote_bbox[3] - quote_bbox[1]

    avatar_y = 240 + quote_height + 160
    content_height = avatar_y + 90
    final_height = max(820, content_height)

    image = Image.new("RGB", (request.width, final_height), theme.canvas_color)
    draw = ImageDraw.Draw(image)

    _draw_title(
        draw=draw,
        text=theme.title,
        font=title_font,
        width=request.width,
        color=theme.accent_color,
    )

    draw_multiline_text_with_local_emoji(
        image=image,
        position=(70, 240),
        text=quote_block,
        font=quote_font,
        fill=theme.text_color,
        spacing=theme.line_spacing,
    )

    avatar_x = 70
    avatar_y = final_height - 220
    avatar_size = 160

    avatar_image = load_circle_avatar(
        avatar_url=message.avatar_url,
        size=avatar_size,
    )

    if avatar_image is not None:
        image.paste(avatar_image, (avatar_x, avatar_y), avatar_image)
    else:
        _draw_placeholder_avatar(
            draw=draw,
            x=avatar_x,
            y=avatar_y,
            size=avatar_size,
            fill=theme.bubble_color,
            text_color=theme.text_color,
        )

    author_text = f"{theme.author_prefix}{message.author_name}{theme.author_suffix}"
    draw.text(
        (avatar_x + avatar_size + 28, avatar_y + avatar_size // 2),
        author_text,
        font=author_font,
        fill=theme.text_color,
        anchor="lm",
    )

    file_path = OUTPUT_DIR / f"single-{uuid4().hex}.png"
    image.save(file_path)
    return file_path


def _draw_title(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    width: int,
    color: tuple[int, int, int],
) -> None:
    draw.text(
        (width // 2, 90),
        text,
        font=font,
        fill=color,
        anchor="ma",
    )


def _draw_placeholder_avatar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int,
    fill: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> None:
    draw.ellipse(
        (x, y, x + size, y + size),
        fill=fill,
    )

    icon_font = ImageFont.load_default()
    draw.text(
        (x + size // 2, y + size // 2),
        ">_",
        font=icon_font,
        fill=text_color,
        anchor="mm",
    )