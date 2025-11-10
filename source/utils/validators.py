# Author: HeartoLazor
# Description: Data validation utilities

import os
from typing import List, Optional, Tuple
from pathlib import Path
from data_models.animation_models import AnimationSet, AnimationData
from config.settings import app_settings

def validate_animation_set(anim_set: AnimationSet) -> Tuple[bool, List[str]]:
    """Validate an AnimationSet and return (is_valid, errors)"""
    errors = []
    
    if not anim_set.animations:
        errors.append("No animations found")
    
    if not anim_set.directory or not os.path.exists(anim_set.directory):
        errors.append(f"Directory doesn't exist: {anim_set.directory}")
    
    # Validate sprite files exist
    for anim in anim_set.animations:
        sprite_path = os.path.join(anim_set.directory, anim.path)
        if not os.path.exists(sprite_path):
            errors.append(f"Missing sprite: {sprite_path}")
        else:
            # Validate sprite dimensions
            sprite_errors = validate_sprite_dimensions(sprite_path, anim)
            errors.extend(sprite_errors)
    
    # Validate frame indices for Stardew animations
    if anim_set.stardew_animations:
        frame_errors = validate_frame_indices(anim_set)
        errors.extend(frame_errors)
    
    return len(errors) == 0, errors

def validate_sprite_dimensions(sprite_path: str, animation: AnimationData) -> List[str]:
    """Validate sprite dimensions match animation data"""
    errors = []
    try:
        from PIL import Image
        with Image.open(sprite_path) as img:
            width, height = img.size
            
            # Check if sprite can be divided into frames properly
            if width % animation.frame_width != 0:
                errors.append(f"Sprite width {width} not divisible by frame width {animation.frame_width} in {animation.name}")
            
            if height % animation.frame_height != 0:
                errors.append(f"Sprite height {height} not divisible by frame height {animation.frame_height} in {animation.name}")
            
            # Check maximum size
            if width > app_settings.MAX_SPRITE_SIZE or height > app_settings.MAX_SPRITE_SIZE:
                errors.append(f"Sprite dimensions {width}x{height} exceed maximum size in {animation.name}")
                
    except Exception as e:
        errors.append(f"Could not validate sprite dimensions for {animation.name}: {e}")
    
    return errors

def validate_frame_indices(anim_set: AnimationSet) -> List[str]:
    """Validate that frame indices are within bounds"""
    errors = []
    
    for stardew_anim in anim_set.stardew_animations:
        pokemon_anim = next((a for a in anim_set.animations 
                           if a.name == stardew_anim.pokemon_anim_name), None)
        
        if not pokemon_anim:
            errors.append(f"Referenced animation not found: {stardew_anim.pokemon_anim_name}")
            continue
            
        # Calculate maximum possible frames (8 directions × frames per direction)
        max_frames = pokemon_anim.total_frames * 8
        
        # Validate all referenced frames
        all_frames = (stardew_anim.pokemon_frames_index_front + 
                     stardew_anim.pokemon_frames_index_right +
                     stardew_anim.pokemon_frames_index_back +
                     stardew_anim.pokemon_frames_index_left)
        
        for frame_idx in all_frames:
            if frame_idx < 0:
                errors.append(f"Negative frame index {frame_idx} in {stardew_anim.stardew_anim_name}")
            elif frame_idx >= max_frames:
                errors.append(f"Frame index {frame_idx} out of bounds (max: {max_frames-1}) in {stardew_anim.stardew_anim_name}")
    
    return errors

def validate_output_directory(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate output directory is writable"""
    errors = []
    
    try:
        # Try to create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test writing a file
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        
    except (PermissionError, OSError) as e:
        errors.append(f"Cannot write to output directory {output_dir}: {e}")
    
    return len(errors) == 0, errors