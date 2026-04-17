from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageOps


def load_circle_avatar(
    avatar_url: str | None,
    size: int,
) -> Image.Image | None:
    if not avatar_url:
        return None

    try:
        response = requests.get(avatar_url, timeout=10)
        response.raise_for_status()

        avatar = Image.open(BytesIO(response.content)).convert("RGB")
        avatar = ImageOps.fit(avatar, (size, size), method=Image.Resampling.LANCZOS)

        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)

        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(avatar, (0, 0))
        result.putalpha(mask)

        return result

    except Exception:
        return None
