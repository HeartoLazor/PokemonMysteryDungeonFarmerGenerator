# Author: HeartoLazor
# Description: Power-of-two texture optimization

import os
import math
from typing import Tuple, Dict
from PIL import Image

def find_nearest_power_of_two(value: int) -> int:
    """
    Find the nearest power of two for a given value
    """
    if value <= 0:
        return 1
    
    # Find the closest power of two
    lower = 2 ** math.floor(math.log2(value))
    upper = 2 ** math.ceil(math.log2(value))
    
    # Choose the closest one
    if abs(value - lower) < abs(value - upper):
        return lower
    else:
        return upper

def find_optimal_pot_layout(frame_width: int, frame_height: int, 
                           total_frames: int, max_texture_size: int = 2048) -> Tuple[int, int, int, int]:
    """
    Find optimal power-of-two layout for spritesheet considering final crop
    """
    # Common power-of-two sizes
    pot_sizes = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    
    best_layout = None
    best_waste = float('inf')
    
    for pot_size in pot_sizes:
        if pot_size > max_texture_size:
            continue
            
        # Calculate how many frames fit
        frames_per_row = pot_size // frame_width
        if frames_per_row == 0:
            continue
            
        frames_per_column = pot_size // frame_height
        if frames_per_column == 0:
            continue
        
        # Calculate required rows
        required_rows = (total_frames + frames_per_row - 1) // frames_per_row
        required_columns = min(frames_per_row, total_frames)
        
        # Calculate actual used dimensions
        used_width = required_columns * frame_width
        used_height = required_rows * frame_height
        
        # Skip if doesn't fit in this POT size
        if used_width > pot_size or used_height > pot_size:
            continue
        
        # Calculate wasted space (transparent areas)
        wasted_space = (pot_size * pot_size) - (used_width * used_height)
        
        # Prefer layouts with less wasted space
        if wasted_space < best_waste:
            best_waste = wasted_space
            best_layout = (pot_size, pot_size, frames_per_row, frames_per_column)
    
    # If no perfect fit found, use fallback
    if not best_layout:
        # Calculate minimum required size
        min_frames_per_row = 1
        while (min_frames_per_row * frame_width < total_frames * frame_height) and (min_frames_per_row < total_frames):
            min_frames_per_row += 1
        
        required_rows = (total_frames + min_frames_per_row - 1) // min_frames_per_row
        required_width = min_frames_per_row * frame_width
        required_height = required_rows * frame_height
        
        # Find smallest POT that can contain this
        for pot_size in pot_sizes:
            if pot_size >= required_width and pot_size >= required_height and pot_size <= max_texture_size:
                frames_per_row = min_frames_per_row
                frames_per_column = pot_size // frame_height
                best_layout = (pot_size, pot_size, frames_per_row, frames_per_column)
                break
    
    # Final fallback: use calculated size rounded to POT
    if not best_layout:
        required_width = ((total_frames + min_frames_per_row - 1) // min_frames_per_row) * frame_width
        required_height = min_frames_per_row * frame_height
        
        texture_width = find_nearest_power_of_two(required_width)
        texture_height = find_nearest_power_of_two(required_height)
        
        texture_width = min(texture_width, max_texture_size)
        texture_height = min(texture_height, max_texture_size)
        
        frames_per_row = texture_width // frame_width
        frames_per_column = texture_height // frame_height
        
        best_layout = (texture_width, texture_height, frames_per_row, frames_per_column)
    
    print(f"📐 Optimal POT layout: {best_layout[0]}x{best_layout[1]}, "
          f"{best_layout[2]} frames/row, {best_layout[3]} frames/column")
    
    return best_layout

def optimize_spritesheet_to_pot(spritesheet_path: str, output_path: str,
                               frame_width: int, frame_height: int,
                               total_frames: int, current_frames_per_row: int,
                               max_texture_size: int = 2048) -> Tuple[int, int, int]:
    """
    Repack spritesheet into power-of-two texture and crop to actual content
    """
    print(f"🎯 Repacking spritesheet into power-of-two texture...")
    
    # Find optimal layout
    texture_width, texture_height, new_frames_per_row, frames_per_column = find_optimal_pot_layout(
        frame_width, frame_height, total_frames, max_texture_size
    )
    
    with Image.open(spritesheet_path) as spritesheet:
        spritesheet = spritesheet.convert('RGBA')
        
        # Create new power-of-two texture (temporal)
        pot_texture = Image.new('RGBA', (texture_width, texture_height), (0, 0, 0, 0))
        
        # Track the bottom coordinate of the lowest frame that has visible content
        max_used_y = 0
        
        # Copy frames to new texture
        for frame_index in range(total_frames):
            # Calculate position in original spritesheet
            orig_row = frame_index // current_frames_per_row
            orig_col = frame_index % current_frames_per_row
            orig_x = orig_col * frame_width
            orig_y = orig_row * frame_height
            
            # Extract frame from original
            frame = spritesheet.crop((orig_x, orig_y, orig_x + frame_width, orig_y + frame_height))
            
            # Calculate position in new POT texture
            new_row = frame_index // new_frames_per_row
            new_col = frame_index % new_frames_per_row
            new_x = new_col * frame_width
            new_y = new_row * frame_height
            
            # Paste frame into new texture
            pot_texture.paste(frame, (new_x, new_y))
            
            # Check if this frame has visible content
            has_visible_content = False
            frame_data = frame.getdata()
            for pixel in frame_data:
                if pixel[3] > 0:  # Alpha channel > 0 means visible
                    has_visible_content = True
                    break
            
            # If frame has visible content, update max_used_y
            if has_visible_content:
                frame_bottom = new_y + frame_height
                if frame_bottom > max_used_y:
                    max_used_y = frame_bottom
        
        # If no frames with visible content found, use the position of the last frame
        if max_used_y == 0:
            last_frame_index = total_frames - 1
            last_row = last_frame_index // new_frames_per_row
            max_used_y = (last_row + 1) * frame_height
            print(f"📝 No visible content found, using last frame position: {max_used_y}")
        else:
            print(f"📝 Lowest frame with content at Y: {max_used_y}")
        
        # Calculate actual content bounds
        # Width: all frames have the same width, so use full row width
        actual_width = new_frames_per_row * frame_width
        
        # Height: use the maximum Y coordinate where we found visible content
        actual_height = max_used_y
        
        # Ensure we don't exceed the original POT texture
        actual_width = min(actual_width, texture_width)
        actual_height = min(actual_height, texture_height)
        
        # Safety check: ensure we have enough height for all frames
        required_min_height = ((total_frames - 1) // new_frames_per_row + 1) * frame_height
        if actual_height < required_min_height:
            print(f"⚠️ Adjusting height to fit all frames: {actual_height} → {required_min_height}")
            actual_height = required_min_height
        
        print(f"📐 Final calculated bounds: {actual_width}x{actual_height}")
        
        # Crop to actual content
        final_texture = pot_texture.crop((0, 0, actual_width, actual_height))
        cropped_width, cropped_height = final_texture.size
        
        print(f"📐 Original POT: {texture_width}x{texture_height}")
        print(f"📐 Final texture: {cropped_width}x{cropped_height}")
        
        # Final verification: ensure no frames are cropped
        last_frame_bottom = ((total_frames - 1) // new_frames_per_row * frame_height) + frame_height
        if cropped_height < last_frame_bottom:
            print(f"❌ ERROR: Would crop frames! Required: {last_frame_bottom}, Got: {cropped_height}")
            print("   Using original POT texture without crop")
            final_texture = pot_texture
            cropped_width, cropped_height = texture_width, texture_height
        
        final_texture.save(output_path, 'PNG')
        
        print(f"✅ Repacked and cropped spritesheet: {cropped_width}x{cropped_height}, "
              f"{new_frames_per_row} frames/row")
        
        return cropped_width, cropped_height, new_frames_per_row

def optimize_texture_pot(output_dir: str, frame_width: int, frame_height: int,
                        total_frames: int, current_frames_per_row: int, 
                        max_texture_size: int = 2048) -> Tuple[int, int, int]:
    """
    Main function to optimize texture to power-of-two dimensions
    """
    print(f"🎯 Optimizing texture to power-of-two: {output_dir}")
    
    spritesheet_path = os.path.join(output_dir, "body.png")
    body_json_path = os.path.join(output_dir, "body.json")
    
    if not os.path.exists(spritesheet_path) or not os.path.exists(body_json_path):
        print(f"⚠️ Skipping POT optimization: required files not found")
        return frame_width, frame_height, current_frames_per_row
        
    # Optimize spritesheet
    temp_spritesheet = os.path.join(output_dir, "body_pot.png")
    new_width, new_height, new_frames_per_row = optimize_spritesheet_to_pot(
        spritesheet_path, temp_spritesheet, frame_width, frame_height,
        total_frames, current_frames_per_row, max_texture_size
    )
    
    # Replace original
    os.replace(temp_spritesheet, spritesheet_path)
    
    print(f"🎉 POT optimization complete: {new_width}x{new_height}, {new_frames_per_row} frames/row")
    
    return new_width, new_height, new_frames_per_row

def batch_pot_optimization(base_output_dir: str, spritesheet_mapping: Dict, max_texture_size: int = 2048) -> Dict:
    """Optimize all spritesheets to power-of-two"""
    print(f"🚀 Starting POT optimization for {len(spritesheet_mapping)} spritesheets...")
    
    updated_mapping = spritesheet_mapping.copy()
    
    for variant_name, sprite_data in spritesheet_mapping.items():
        output_dir = sprite_data['directory']
        frame_width = sprite_data['max_width']
        frame_height = sprite_data['max_height']
        total_frames = sprite_data['total_frames']
        current_frames_per_row = sprite_data.get('frames_per_row', 32)
        
        print(f"\n--- POT Optimization: {variant_name} ---")
        try:
            new_width, new_height, new_frames_per_row = optimize_texture_pot(
                output_dir, frame_width, frame_height, total_frames, 
                current_frames_per_row, max_texture_size
            )
            
            # Update mapping
            updated_mapping[variant_name]['max_width'] = frame_width
            updated_mapping[variant_name]['max_height'] = frame_height
            updated_mapping[variant_name]['frames_per_row'] = new_frames_per_row
            
            print(f"✅ Updated {variant_name}: {new_width}x{new_height}, {new_frames_per_row} frames/row")
            
        except Exception as e:
            print(f"❌ POT optimization failed for {variant_name}: {e}")
    
    print(f"\n🎊 POT optimization completed!")
    return updated_mapping