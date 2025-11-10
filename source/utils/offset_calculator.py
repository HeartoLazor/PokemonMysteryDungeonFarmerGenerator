# Author: HeartoLazor
# Description: Sprite offset calculation

import os
from pathlib import Path
from PIL import Image
from data_models.animation_models import AnimationSet
from .image_utils import find_foot_average, find_white_point
from config.settings import app_settings

def calculate_sprite_offsets(anim_set: AnimationSet, max_width: int, max_height: int) -> tuple:
    reference_paths = [
        app_settings.IMAGES_DIR / "body_position_references.png",
        Path("./images/body_position_references.png"),
        Path("images/body_position_references.png"), 
        Path(__file__).parent.parent / "images" / "body_position_references.png"
    ]
    
    reference_path = None
    for path in reference_paths:
        if path.exists():
            reference_path = path
            break
    
    if not reference_path:
        print(f"⚠️ body_position_references.png not found")
        return 0, 0, 0
    
    try:
        reference_sprite = Image.open(reference_path).convert('RGBA')
        REFERENCE_WIDTH, REFERENCE_HEIGHT = reference_sprite.size
        REFERENCE_CENTER_X = REFERENCE_WIDTH // 2
        REFERENCE_CENTER_Y = REFERENCE_HEIGHT // 2
        
        print(f"📐 Reference sprite: {REFERENCE_WIDTH}x{REFERENCE_HEIGHT}, center: ({REFERENCE_CENTER_X}, {REFERENCE_CENTER_Y})")
        
        pokemon_center_x = max_width // 2
        pokemon_center_y = max_height // 2
        
        offset_x = pokemon_center_x - REFERENCE_CENTER_X
        offset_y = pokemon_center_y - REFERENCE_CENTER_Y
        
        foot_difference = calculate_foot_difference(anim_set, max_width, max_height, reference_path)
        if foot_difference != 0:
            offset_y -= foot_difference
        
        print(f"🎯 Calculated offsets: X={offset_x}, Y={offset_y}, Foot Difference: {foot_difference}")
        
        return offset_x, offset_y, foot_difference
        
    except Exception as e:
        print(f"❌ Error calculating sprite offsets: {e}")
        return 0, 0, 0

def calculate_foot_difference(anim_set: AnimationSet, max_width: int, max_height: int, reference_path: str) -> int:


    shadow_path = None
    for animation in anim_set.animations:
        if animation.name == "Idle":     
            shadow_path = os.path.join(anim_set.directory, animation.shadow_path)


    if not os.path.exists(shadow_path):
        print(f"⚠️ {shadow_path} path not found for {anim_set.variant_name}")
        return 0
    
    if not shadow_path:
        print(f"⚠️ Idle not found for {anim_set.variant_name}")
        return 0
    
    try:
        shadow_sprite = Image.open(shadow_path).convert('RGBA')
        reference_sprite = Image.open(reference_path).convert('RGBA')
        
        idle_anim = next((a for a in anim_set.animations if a.name.lower() == "idle"), None)
        if idle_anim and idle_anim.frame_width > 0:
            frame_width = idle_anim.frame_width
            frame_height = idle_anim.frame_height
        else:
            frame_width, frame_height = shadow_sprite.size
        
        first_frame = shadow_sprite.crop((0, 0, frame_width, frame_height))
        
        centered_pokemon_frame = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
        pokemon_offset_x = (max_width - frame_width) // 2
        pokemon_offset_y = (max_height - frame_height) // 2
        centered_pokemon_frame.paste(first_frame, (pokemon_offset_x, pokemon_offset_y))
        
        centered_reference_frame = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
        ref_width, ref_height = reference_sprite.size
        ref_offset_x = (max_width - ref_width) // 2
        ref_offset_y = (max_height - ref_height) // 2
        centered_reference_frame.paste(reference_sprite, (ref_offset_x, ref_offset_y))
        
        pokemon_white_point = find_white_point(centered_pokemon_frame, max_width, max_height)
        if pokemon_white_point is None:
            print(f"⚠️ No white point found in {shadow_path}")
            return 0
        
        pokemon_foot_position = pokemon_white_point + 1
        
        reference_foot_avg = find_foot_average(centered_reference_frame, max_width, max_height)
        if reference_foot_avg is None:
            print(f"⚠️ No foot pixels found in reference")
            return 0
        
        foot_difference = reference_foot_avg - pokemon_foot_position
        
        print(f"👣 Foot difference: {foot_difference} (Pokémon white point: {pokemon_white_point} + 1 = {pokemon_foot_position}, Reference: {reference_foot_avg})")
        
        return foot_difference
        
    except Exception as e:
        print(f"❌ Error calculating foot difference: {e}")
        return 0