# Author: HeartoLazor
# Description: Frame deduplication and optimization

import os
import json
from PIL import Image
from typing import Dict, List, Tuple

def compare_frames_pixel_by_pixel(frame1: Image.Image, frame2: Image.Image, tolerance: int = 0) -> bool:
    """
    Compare two frames pixel by pixel with optional tolerance
    """
    if frame1.size != frame2.size:
        return False
    
    # Convert both to RGBA for consistent comparison
    frame1_rgba = frame1.convert('RGBA')
    frame2_rgba = frame2.convert('RGBA')
    
    pixels1 = frame1_rgba.load()
    pixels2 = frame2_rgba.load()
    
    width, height = frame1_rgba.size
    
    for y in range(height):
        for x in range(width):
            r1, g1, b1, a1 = pixels1[x, y]
            r2, g2, b2, a2 = pixels2[x, y]
            
            # Check if pixels are different beyond tolerance
            if (abs(r1 - r2) > tolerance or 
                abs(g1 - g2) > tolerance or 
                abs(b1 - b2) > tolerance or 
                abs(a1 - a2) > tolerance):
                return False
    
    return True

def find_duplicate_frames(spritesheet_path: str, frame_width: int, frame_height: int, 
                         total_frames: int, frames_per_row: int, tolerance: int = 0) -> Dict[int, List[int]]:
    """
    Find duplicate frames using direct pixel comparison
    """
    print(f"🔍 Searching for duplicate frames in {spritesheet_path}...")
    
    with Image.open(spritesheet_path) as spritesheet:
        spritesheet = spritesheet.convert('RGBA')
        
        frames = {}  # Store frame objects for comparison
        duplicates = {}
        skipped_frames = set()
        
        frames_processed = 0
        comparisons_made = 0
        
        # First pass: load all frames
        for frame_index in range(total_frames):
            if frame_index in skipped_frames:
                continue
                
            row = frame_index // frames_per_row
            col = frame_index % frames_per_row
            
            x_start = col * frame_width
            y_start = row * frame_height
            x_end = x_start + frame_width
            y_end = y_start + frame_height
            
            if (x_end > spritesheet.width or y_end > spritesheet.height):
                continue
            
            frame = spritesheet.crop((x_start, y_start, x_end, y_end))
            frames[frame_index] = frame
            frames_processed += 1
        
        print(f"📥 Loaded {frames_processed} frames for comparison")
        
        # Second pass: compare frames
        frame_indices = list(frames.keys())
        
        for i in range(len(frame_indices)):
            current_idx = frame_indices[i]
            
            if current_idx in skipped_frames:
                continue
                
            current_frame = frames[current_idx]
            current_duplicates = []
            
            for j in range(i + 1, len(frame_indices)):
                compare_idx = frame_indices[j]
                
                if compare_idx in skipped_frames:
                    continue
                
                compare_frame = frames[compare_idx]
                comparisons_made += 1
                
                if compare_frames_pixel_by_pixel(current_frame, compare_frame, tolerance):
                    current_duplicates.append(compare_idx)
                    skipped_frames.add(compare_idx)
                    print(f"  🔄 Frame {compare_idx} is duplicate of {current_idx}")
            
            if current_duplicates:
                duplicates[current_idx] = current_duplicates
        
        print(f"📊 Made {comparisons_made} comparisons, found {len(duplicates)} sets of duplicates")
        
        for base_frame, dupes in duplicates.items():
            print(f"  🎯 Frame {base_frame} has {len(dupes)} duplicates: {dupes}")
        
        return duplicates

def debug_compare_specific_frames(spritesheet_path: str, frame_indices: List[int], 
                                 frame_width: int, frame_height: int, frames_per_row: int):
    """
    Debug: compare specific frames in detail
    """
    print(f"🐛 DEBUG: Detailed comparison of frames {frame_indices}")
    
    with Image.open(spritesheet_path) as spritesheet:
        spritesheet = spritesheet.convert('RGBA')
        
        frames = []
        for idx in frame_indices:
            row = idx // frames_per_row
            col = idx % frames_per_row
            x_start = col * frame_width
            y_start = row * frame_height
            frame = spritesheet.crop((x_start, y_start, x_start + frame_width, y_start + frame_height))
            frames.append((idx, frame))
        
        # Compare each pair
        for i in range(len(frames)):
            for j in range(i + 1, len(frames)):
                idx1, frame1 = frames[i]
                idx2, frame2 = frames[j]
                
                are_identical = compare_frames_pixel_by_pixel(frame1, frame2)
                print(f"  Frames {idx1} vs {idx2}: {are_identical}")
                
                if not are_identical:
                    # Find the first differing pixel
                    pixels1 = frame1.load()
                    pixels2 = frame2.load()
                    width, height = frame1.size
                    
                    for y in range(height):
                        for x in range(width):
                            if pixels1[x, y] != pixels2[x, y]:
                                print(f"    First difference at ({x},{y}): {pixels1[x, y]} vs {pixels2[x, y]}")
                                return

def create_optimized_spritesheet(spritesheet_path: str, output_path: str, 
                                frame_width: int, frame_height: int,
                                total_frames: int, frames_per_row: int,
                                duplicates: Dict[int, List[int]]) -> Tuple[int, Dict[int, int]]:
    """
    Create optimized spritesheet removing duplicate frames and renumbering
    """
    print("🔄 Creating optimized spritesheet...")
    
    # Check all non duplicated frames to be saved
    all_frames_to_keep = set(range(total_frames))
    frames_to_remove = set()
    
    for base_frame, dupes in duplicates.items():
        frames_to_remove.update(dupes)
    
    # Save all frames with the exeption of duplicated ones
    frames_to_keep = sorted(list(all_frames_to_keep - frames_to_remove))
    new_total_frames = len(frames_to_keep)
    
    print(f"📊 Keeping {new_total_frames} unique frames, removing {len(frames_to_remove)} duplicates")
    
    # Create mapping: original_frame -> new_frame
    frame_mapping = {}
    for new_index, original_index in enumerate(frames_to_keep):
        frame_mapping[original_index] = new_index
    
    # Map duplicated to their base frames
    for base_frame, dupes in duplicates.items():
        if base_frame in frame_mapping:
            for dupe in dupes:
                frame_mapping[dupe] = frame_mapping[base_frame]
    
    # Calculate new spritesheet size
    rows_needed = (new_total_frames + frames_per_row - 1) // frames_per_row
    new_sheet_width = frame_width * frames_per_row
    new_sheet_height = frame_height * rows_needed
    
    with Image.open(spritesheet_path) as spritesheet:
        spritesheet = spritesheet.convert('RGBA')
        optimized_sheet = Image.new('RGBA', (new_sheet_width, new_sheet_height), (0, 0, 0, 0))
        
        # Copy unique frames in order
        for new_index, original_index in enumerate(frames_to_keep):
            row = original_index // frames_per_row
            col = original_index % frames_per_row
            
            # Position in the original spritesheet
            x_start = col * frame_width
            y_start = row * frame_height
            x_end = x_start + frame_width
            y_end = y_start + frame_height
            
            if (x_end > spritesheet.width or y_end > spritesheet.height):
                continue
            
            frame = spritesheet.crop((x_start, y_start, x_end, y_end))
            
            # Position in the new spritesheet
            new_row = new_index // frames_per_row
            new_col = new_index % frames_per_row
            new_x = new_col * frame_width
            new_y = new_row * frame_height
            
            optimized_sheet.paste(frame, (new_x, new_y))
        
        print(f"✅ Copied {len(frames_to_keep)} unique frames to new spritesheet")
    
    optimized_sheet.save(output_path, 'PNG')
    print(f"✅ Optimized spritesheet: {total_frames} → {new_total_frames} frames")
    
    # Debug: show mapping
    print("📋 Frame mapping:")
    for original, new in sorted(frame_mapping.items()):
        if original != new:
            print(f"  {original} → {new}")
    
    return new_total_frames, frame_mapping

def update_json_frame_references(body_json_path: str, frame_mapping: Dict[int, int]):
    """Update frame numbers in JSON to use deduplicated references"""
    print(f"📝 Updating JSON frame references...")
    
    with open(body_json_path, 'r', encoding='utf-8') as f:
        body_data = json.load(f)
    
    frames_updated = 0
    
    def update_animation_frames(animations):
        nonlocal frames_updated
        for anim in animations:
            if 'Frame' in anim:
                original_frame = anim['Frame']
                if original_frame in frame_mapping:
                    new_frame = frame_mapping[original_frame]
                    if new_frame != original_frame:
                        anim['Frame'] = new_frame
                        frames_updated += 1
                        print(f"    {original_frame} → {new_frame}")

    for body_type in ['FrontBody', 'RightBody', 'BackBody', 'LeftBody']:
        if body_type in body_data:
            print(f"  Updating {body_type}:")
            
            if 'IdleAnimation' in body_data[body_type]:
                update_animation_frames(body_data[body_type]['IdleAnimation'])
            if 'MovementAnimation' in body_data[body_type]:
                update_animation_frames(body_data[body_type]['MovementAnimation'])

    # Save updated JSON
    with open(body_json_path, 'w', encoding='utf-8') as f:
        json.dump(body_data, f, indent=2)
    
    print(f"✅ Updated {frames_updated} frame references in JSON")

def deduplicate_frames(output_dir: str, frame_width: int, frame_height: int, 
                      total_frames: int, frames_per_row: int = 32, tolerance: int = 0) -> int:
    """Main function to deduplicate frames in a sprite output"""
    print(f"🎯 Deduplicating frames in: {output_dir}")
    
    spritesheet_path = os.path.join(output_dir, "body.png")
    body_json_path = os.path.join(output_dir, "body.json")
    
    if not os.path.exists(spritesheet_path) or not os.path.exists(body_json_path):
        print(f"⚠️ Skipping deduplication: required files not found")
        return total_frames
    
    # Find duplicates
    duplicates = find_duplicate_frames(spritesheet_path, frame_width, frame_height, 
                                     total_frames, frames_per_row, tolerance)
    
    if not duplicates:
        print("ℹ️ No duplicate frames found")
        return total_frames
    
    # Create optimized spritesheet
    temp_spritesheet = os.path.join(output_dir, "body_deduped.png")
    new_total_frames, frame_mapping = create_optimized_spritesheet(
        spritesheet_path, temp_spritesheet, frame_width, frame_height,
        total_frames, frames_per_row, duplicates
    )
    
    # Replace original
    os.replace(temp_spritesheet, spritesheet_path)
    
    # Update JSON
    update_json_frame_references(body_json_path, frame_mapping)
    
    print(f"🎉 Deduplication complete: {total_frames} → {new_total_frames} frames")
    
    return new_total_frames

def batch_deduplicate_frames(base_output_dir: str, spritesheet_mapping: Dict) -> Dict:
    """Deduplicate frames for all generated spritesheets"""
    print(f"🚀 Starting frame deduplication for {len(spritesheet_mapping)} spritesheets...")
    
    updated_mapping = spritesheet_mapping.copy()
    
    for variant_name, sprite_data in spritesheet_mapping.items():
        output_dir = sprite_data['directory']
        frame_width = sprite_data['max_width']
        frame_height = sprite_data['max_height']
        total_frames = sprite_data['total_frames']
        frames_per_row = sprite_data.get('frames_per_row', 32)
        
        print(f"\n--- Deduplicating {variant_name} ---")
        try:
            new_total_frames = deduplicate_frames(output_dir, frame_width, frame_height, total_frames, frames_per_row)
            
            if new_total_frames and new_total_frames != total_frames:
                updated_mapping[variant_name]['total_frames'] = new_total_frames
                print(f"✅ Updated {variant_name}: {total_frames} → {new_total_frames} frames")
            else:
                print(f"ℹ️ No frame reduction for {variant_name}")
                
        except Exception as e:
            print(f"❌ Deduplication failed for {variant_name}: {e}")
    
    print(f"\n🎊 Frame deduplication completed!")
    return updated_mapping
