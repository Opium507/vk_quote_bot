from pathlib import Path
from PIL import ImageFont
from app.logger import logger

def load_font(font_path: str, size: int):
    """
    Загружает шрифт из указанного пути.
    Если шрифт не найден или повреждён, возвращает стандартный шрифт PIL.
    """
    try:
        path = Path(font_path)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    except Exception as e:
        logger.warning(f"Ошибка загрузки шрифта {font_path}: {e}")
    return ImageFont.load_default()