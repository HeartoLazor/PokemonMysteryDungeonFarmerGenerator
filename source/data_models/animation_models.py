# Author: HeartoLazor
# Description: Data models for animations and mappings

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .enums import StardewAnimationDataModes, StardewBodyModelType
from PIL import Image

@dataclass
class StardewAnimationData:
    stardew_anim_name: str
    fallback_names: List[str]
    use_front_only: bool = False
    flip_left_frames: bool = True
    duration_mult: float = 1.0
    conditions_names: List[str] = field(default_factory=list)
    conditions_group_names: List[str] = field(default_factory=list)
    end_when_farmer_frame_updates: bool = False
    body_type: StardewBodyModelType = StardewBodyModelType.movement_animation
    mode: StardewAnimationDataModes = StardewAnimationDataModes.default
    debug_font_color: tuple = (255, 255, 255)
    discard_distance: int = 0
    sprite_offset_x: int = 0
    sprite_offset_y: int = 0
    portrait_offset_x: int = 0
    portrait_offset_y: int = 0

@dataclass
class StardewAnimationDefault(StardewAnimationData):
    pass

@dataclass
class StardewAnimationForceFrame(StardewAnimationData):
    frame: int = 0
    
    def __post_init__(self):
        self.mode = StardewAnimationDataModes.force_frame

@dataclass
class StardewAnimationRangeStartEnd(StardewAnimationData):
    frame_start: int = 0
    frame_end: int = 0

    def __post_init__(self):
        self.mode = StardewAnimationDataModes.range_start_end

@dataclass
class StardewAnimationRangeStartNegativeEnd(StardewAnimationData):
    frame_range_start: List[int] = field(default_factory=list)
    frame_range_end: List[int] = field(default_factory=list)

    def __post_init__(self):
        self.mode = StardewAnimationDataModes.range_start_negative_end

@dataclass
class StardewAnimationPortrait(StardewAnimationData):

    frame: int = 0
    def __post_init__(self):
        self.mode = StardewAnimationDataModes.portrait

@dataclass
class StardewAnimationRepeatFrameCount(StardewAnimationData):
    frame_quantity: int = 0

    def __post_init__(self):
        self.mode = StardewAnimationDataModes.repeat_frame_count

@dataclass
class AnimationData:
    name: str
    anim_path: str
    offsets_path: str
    shadow_path: str
    frame_width: int
    frame_height: int
    durations: List[int]
    total_frames: int = 0

@dataclass
class StardewMap:
    stardew_anim_name: str
    pokemon_anim_name: str
    stardew_map: StardewAnimationData
    pokemon_frames_index_front: List[int] = field(default_factory=list)
    pokemon_frames_index_right: List[int] = field(default_factory=list)
    pokemon_frames_index_back: List[int] = field(default_factory=list)
    pokemon_frames_index_left: List[int] = field(default_factory=list)
    reuses_frames_from: Optional[str] = None

@dataclass
class AnimationSet:
    pokemon_id: str
    pokemon_name: str
    variant_name: str
    generation: str
    directory: str
    max_width: int
    max_height: int
    animations: List[AnimationData] = field(default_factory=list)
    stardew_animations: List[StardewMap] = field(default_factory=list)
    global_offsets: Dict = field(default_factory=dict)

    def calculate_frame_indices(self, animation: AnimationData, stardew_map: StardewAnimationData) -> Dict[str, List[int]]:
        total_frames = animation.total_frames
        
        sprite_path = os.path.join(self.directory, animation.anim_path)
        actual_rows = 8
        frames_per_row = total_frames
        
        try:
            with Image.open(sprite_path) as sprite:
                sprite_height = sprite.height
                sprite_width = sprite.width
                
                actual_rows = sprite_height // animation.frame_height
                frames_per_row = sprite_width // animation.frame_width
                
                if frames_per_row < total_frames:
                    total_frames = frames_per_row
                
                print(f"📊 {animation.name}: {actual_rows} rows, {frames_per_row} frames per row")
                
        except Exception as e:
            print(f"⚠️ Could not open sprite {sprite_path} to determine rows: {e}")
        
        base_indices = {
            'front': 0,
            'diagonal_down_right': total_frames * 1,
            'right': total_frames * 2,
            'diagonal_up_right': total_frames * 3,
            'back': total_frames * 4,
            'diagonal_up_left': total_frames * 5,
            'left': total_frames * 6,
            'diagonal_down_left': total_frames * 7
        }
        
        def get_frame_sequence(mode, base_idx, frames_count):
            # For ALL modes, return the actual frames that should be in the spritesheet
            # The special logic (repetition, specific frame selection) will be handled in JSON generation
            if mode == StardewAnimationDataModes.default:
                return list(range(base_idx, base_idx + frames_count))
                
            elif mode == StardewAnimationDataModes.force_frame:
                # Include only the forced frame in spritesheet
                frame_idx = min(stardew_map.frame, frames_count - 1)
                return [base_idx + frame_idx]
                
            elif mode == StardewAnimationDataModes.range_start_end:
                # Include the range in spritesheet
                start = min(stardew_map.frame_start, frames_count - 1)
                end = min(stardew_map.frame_end, frames_count - 1)
                return list(range(base_idx + start, base_idx + end + 1))
                
            elif mode == StardewAnimationDataModes.range_start_negative_end:
                # Include all frames in spritesheet, selection handled in JSON
                return list(range(base_idx, base_idx + frames_count))
                
            elif mode == StardewAnimationDataModes.portrait:
                # Include only the portrait frame in spritesheet
                frame_idx = min(stardew_map.frame, frames_count - 1)
                return [base_idx + frame_idx]
                
            elif mode == StardewAnimationDataModes.repeat_frame_count:
                # Include all frames in spritesheet, repetition handled in JSON
                return list(range(base_idx, base_idx + frames_count))
                    
            return []

        frames_available = total_frames
        
        if stardew_map.use_front_only:
            front_frames = get_frame_sequence(stardew_map.mode, base_indices['front'], frames_available)
            return {
                'front': front_frames,
                'right': [],
                'back': [],
                'left': []
            }
        else:
            front_frames = get_frame_sequence(stardew_map.mode, base_indices['front'], frames_available)
            
            if actual_rows >= 3:
                right_frames = get_frame_sequence(stardew_map.mode, base_indices['right'], frames_available)
                print(f"  ✅ {animation.name}: Using actual right frames (row 3 available)")
            else:
                right_frames = front_frames
                print(f"  🔄 {animation.name}: Reusing front frames for right (only {actual_rows} rows)")
                
            if actual_rows >= 5:
                back_frames = get_frame_sequence(stardew_map.mode, base_indices['back'], frames_available)
                print(f"  ✅ {animation.name}: Using actual back frames (row 5 available)")
            else:
                back_frames = front_frames
                print(f"  🔄 {animation.name}: Reusing front frames for back (only {actual_rows} rows)")
                
            if actual_rows >= 7:
                left_frames = get_frame_sequence(stardew_map.mode, base_indices['left'], frames_available)
                print(f"  ✅ {animation.name}: Using actual left frames (row 7 available)")
            else:
                left_frames = front_frames
                print(f"  🔄 {animation.name}: Reusing front frames for left (only {actual_rows} rows)")
            
            return {
                'front': front_frames,
                'right': right_frames,
                'back': back_frames,
                'left': left_frames
            }

    def calculate_width_difference(self, anim1: AnimationData, anim2: AnimationData) -> float:
        if not anim1 or not anim2:
            return 0.0
        
        width_diff = abs(anim2.frame_width - anim1.frame_width)
        return width_diff / 2.0

    def filter_animations_for_stardew(self, pokemon_id: str, log_file="stardew_missing.log"):
        from config.stardew_config import load_stardew_mapping_config
        
        is_custom = self.pokemon_id == "-1"
        stardew_mapping, global_offsets = load_stardew_mapping_config(pokemon_id, self.pokemon_name, is_custom)
        
        filtered_list = []
        with open(log_file, "a", encoding="utf-8") as log:
            for entry in stardew_mapping:
                stardew_anim_name = entry.stardew_anim_name
                fallbacks = entry.fallback_names
                found = False
                
                last_fallback_anim = None
                for fallback_name in reversed(fallbacks):
                    last_fallback_anim = next((a for a in self.animations if a.name == fallback_name), None)
                    if last_fallback_anim:
                        break
                
                if not last_fallback_anim:
                    for fallback_name in fallbacks:
                        last_fallback_anim = next((a for a in self.animations if a.name == fallback_name), None)
                        if last_fallback_anim:
                            break
                
                selected_anim = None
                for fallback_name in fallbacks:
                    anim = next((a for a in self.animations if a.name == fallback_name), None)
                    if anim:
                        if entry.discard_distance <= 0:
                            selected_anim = anim
                            break
                        
                        if last_fallback_anim:
                            width_diff = self.calculate_width_difference(last_fallback_anim, anim)
                            
                            if width_diff <= entry.discard_distance:
                                selected_anim = anim
                                print(f"  ✅ {stardew_anim_name}: Selected '{anim.name}' (width diff: {width_diff:.1f} <= {entry.discard_distance})")
                                break
                            else:
                                print(f"  ⚠️ {stardew_anim_name}: Discarded '{anim.name}' (width diff: {width_diff:.1f} > {entry.discard_distance})")
                        else:
                            selected_anim = anim
                            break
                
                if not selected_anim and last_fallback_anim:
                    selected_anim = last_fallback_anim
                    print(f"  🔄 {stardew_anim_name}: Using last fallback '{selected_anim.name}' (no suitable animation found)")
                
                if selected_anim:
                    frame_indices = self.calculate_frame_indices(selected_anim, entry)
                    
                    filtered_list.append(
                        StardewMap(
                            stardew_anim_name=entry.stardew_anim_name, 
                            pokemon_anim_name=selected_anim.name,
                            stardew_map=entry,
                            pokemon_frames_index_front=frame_indices['front'],
                            pokemon_frames_index_right=frame_indices['right'],
                            pokemon_frames_index_back=frame_indices['back'],
                            pokemon_frames_index_left=frame_indices['left']
                        ))
                    found = True
                else:
                    log.write(f"{self.variant_name}: Missing Pokémon animation for Stardew '{stardew_anim_name}' with fallbacks {fallbacks}\n")
        self.stardew_animations = filtered_list
        return global_offsets