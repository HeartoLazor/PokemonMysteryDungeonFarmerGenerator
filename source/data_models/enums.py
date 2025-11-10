# Author: HeartoLazor
# Description: Application enumeration types

from enum import Enum

class StardewAnimationDataModes(Enum):
    default = 0
    force_frame = 1
    range_start_end = 2
    range_start_negative_end = 3
    portrait = 4
    repeat_frame_count = 5

class StardewBodyModelType(Enum):
    idle_animation = 0
    movement_animation = 1
    portrait = 2

class VariantProcessingMode(Enum):
    ALL_VARIANTS = "all-variants"           # Process all variants
    MINIMAL_VARIANTS = "minimal-variants"   # Only process minimal_variations from CSV, defined by the minimal variants column, where 1 is enabled and 0 is disabled
    SKIP_VARIANTS = "skip-variants"         # Only base sprite
    
    def __str__(self):
        return self.value
