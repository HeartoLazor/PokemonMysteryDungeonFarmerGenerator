# Author: HeartoLazor
# Description: Template file loader

from pathlib import Path
from config.settings import app_settings

def load_template(template_name: str) -> str:
    template_paths = [
        app_settings.TEMPLATES_DIR / template_name,
        Path("./templates") / template_name,
        Path("templates") / template_name,
        Path(__file__).parent.parent / "templates" / template_name
    ]
    
    for template_path in template_paths:
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    raise FileNotFoundError(f"Template '{template_name}' not found in any of the expected locations")