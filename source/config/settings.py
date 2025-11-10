# Author: HeartoLazor
# Description: Application settings and configuration

from pathlib import Path
from dataclasses import dataclass

@dataclass
class AppSettings:
    # Paths
    BASE_DIR: Path = Path(".")
    OUTPUT_DIR: Path = Path("generated")
    OUTPUT_DEBUG_DIR: Path = Path("generated_debug")
    TEMPLATES_DIR: Path = Path("templates")
    CONFIG_DIR: Path = Path("generator_configs")
    FONTS_DIR: Path = Path("fonts")
    IMAGES_DIR: Path = Path("images")
    
    # Processing
    FRAMES_PER_ROW: int = 32
    MAX_WORKERS: int = 4
    DEFAULT_FONT_SIZE: int = 16
    
    # Debug
    ENABLE_DEBUG_FRAMES: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Validation
    MAX_SPRITE_SIZE: int = 8192
    
    # Animation
    POKEMON_SPRITES_SUB_DIRECTORY: str = "pokemon"
    CUSTOM_SPRITES_SUB_DIRECTORY: str = "custom"
    NAME_SEPARATOR: str = " - "
    
    @classmethod
    def from_args(cls, args) -> 'AppSettings':
        """Create settings from command line arguments"""
        settings = cls()
        settings.OUTPUT_DIR = Path(args.output)
        settings.FRAMES_PER_ROW = args.frames_per_row
        settings.ENABLE_DEBUG_FRAMES = args.debug_frames
        settings.MAX_WORKERS = args.workers
        
        # Set debug output directory if debug mode is enabled
        if args.debug_frames:
            settings.OUTPUT_DIR = settings.OUTPUT_DEBUG_DIR
        
        settings.OUTPUT_DIR = settings.OUTPUT_DIR / args.variant_mode.value
            
        return settings

# Global settings instance
app_settings = AppSettings()