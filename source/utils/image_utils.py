# Author: HeartoLazor
# Description: Image processing utilities

from pathlib import Path
from PIL import Image, ImageFont
from config.debug_config import DEBUG_CONFIG
from config.settings import app_settings

def load_pixel_font():
    """Load the pixel font with proper settings for crisp rendering using app settings."""
    font_paths = [
        app_settings.FONTS_DIR / "heartolazor_5px_numbers.ttf",
        Path("./fonts/heartolazor_5px_numbers.ttf"),
        Path("fonts/heartolazor_5px_numbers.ttf"),
        Path(__file__).parent.parent / "fonts" / "heartolazor_5px_numbers.ttf"
    ]
    
    for font_path in font_paths:
        try:
            if font_path.exists():
                font = ImageFont.truetype(font_path, DEBUG_CONFIG['font_size'])
                return font
        except Exception as e:
            continue
    
    try:
        return ImageFont.load_default()
    except:
        return None

def find_foot_average(image: Image.Image, width: int, height: int):
    data = image.load()
    left_foot_pos = None
    right_foot_pos = None
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = data[x, y]
            if a > 0:
                if r == 255 and g == 0 and b == 0:
                    left_foot_pos = y
                elif r == 0 and g == 0 and b == 255:
                    right_foot_pos = y
                elif r == 255 and g == 0 and b == 255:
                    left_foot_pos = y
                    right_foot_pos = y
                elif r == 255 and b == 255:
                    left_foot_pos = y
                    right_foot_pos = y
    
    if left_foot_pos is None and right_foot_pos is None:
        return None
    
    if left_foot_pos is not None and right_foot_pos is not None:
        return (left_foot_pos + right_foot_pos) // 2
    elif left_foot_pos is not None:
        return left_foot_pos
    else:
        return right_foot_pos

def find_white_point(image: Image.Image, width: int, height: int):
    data = image.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = data[x, y]
            if a > 0:
                if r == 255 and g == 255 and b == 255:
                    return y
    
    return None