# Author: HeartoLazor
# Description: Sprite processing and spritesheet generation

import os
import shutil
from pathlib import Path
from typing import List
from PIL import Image, ImageOps, ImageDraw
from data_models.animation_models import AnimationData
from config.debug_config import DEBUG_CONFIG
from utils.image_utils import load_pixel_font
from utils.offset_calculator import calculate_sprite_offsets
from .draw_utils import draw_debug_text
from file_handlers.json_generator import generate_body_json
from collections import defaultdict
from config.settings import app_settings
from utils.path_utils import extract_base_variant_name

def generate_spritesheets(sets_with_variation_data: list, output_base_dir: str = "generated", frames_per_row: int = 32, debug_frames: bool = False, variations_as_subfolders: bool = True):
   
    os.makedirs(output_base_dir, exist_ok=True)
    
    spritesheet_mapping = {}
    
    # Dictionary to track frame mapping for debug
    frame_mapping_data = {} 

    debug_font = load_pixel_font() if debug_frames else None
    
    pokemon_variants = defaultdict(list)
    
    eyes_source_paths = [
        app_settings.IMAGES_DIR / "eyes.png",
        Path("./images/eyes.png"),
        Path("images/eyes.png"),
        Path(__file__).parent.parent / "images" / "eyes.png"
    ]
    
    eyes_source_path = None
    for path in eyes_source_paths:
        if path.exists():
            eyes_source_path = path
            break
    
    if not eyes_source_path:
        print("⚠️ eyes.png file not found in any expected location")
    else:
        print(f"✅ Found eyes.png at: {eyes_source_path}")
    
    for data in sets_with_variation_data:
        anim_set = data['anim_set']
        pokemon_variants[anim_set.pokemon_id].append(data)
    
    for pokemon_id, variants_data in pokemon_variants.items():
        variants_data_sorted = sorted(variants_data, key=lambda x: x['anim_set'].variant_name)
        base_data = variants_data_sorted[0]
        base_anim_set = base_data['anim_set']
        base_variation_type = base_data.get('variation_type')
        base_variant_name = extract_base_variant_name(base_anim_set.variant_name, base_variation_type)
        
        for i, data in enumerate(variants_data_sorted):
            anim_set = data['anim_set']
            variation_type = data.get('variation_type')
            
            if not anim_set.stardew_animations:
                print(f"⏭️ Skipping {anim_set.variant_name}: no Stardew animations found")
                continue

            current_base_name = extract_base_variant_name(anim_set.variant_name, variation_type)
            is_base_variant = (current_base_name == base_variant_name and not variation_type)
            
            if variations_as_subfolders:
                main_pokemon_dir = Path(output_base_dir) / base_variant_name
                
                if is_base_variant:
                    output_dir = main_pokemon_dir
                    print(f"📁 Base variant: {anim_set.variant_name} → {output_dir}")
                else:
                    output_dir = main_pokemon_dir / anim_set.variant_name
                    print(f"📁 Variant: {anim_set.variant_name} → {output_dir}")
            else:
                output_dir = Path(output_base_dir) / anim_set.variant_name
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            credit_source_path = os.path.join(anim_set.directory, "credits.txt")
            credit_dest_path = os.path.join(output_dir, "credits.txt")
            if os.path.exists(credit_source_path):
                shutil.copy2(credit_source_path, credit_dest_path)
                print(f"✅ Copied credits.txt: {credit_dest_path}")
            
            if eyes_source_path:
                eyes_dest_path = os.path.join(output_dir, "eyes.png")
                try:
                    shutil.copy2(eyes_source_path, eyes_dest_path)
                    print(f"✅ Copied eyes.png: {eyes_dest_path}")
                except Exception as e:
                    print(f"⚠️ Error copying eyes.png to {eyes_dest_path}: {e}")
            
            offset_x, offset_y, foot_difference = calculate_sprite_offsets(anim_set, anim_set.max_width, anim_set.max_height)
            
            global_offsets = anim_set.global_offsets
            pokemon_sprite_offset_x = global_offsets.get("pokemon_sprite_offset_x", 0)
            pokemon_sprite_offset_y = global_offsets.get("pokemon_sprite_offset_y", 0)
            pokemon_portrait_offset_x = global_offsets.get("pokemon_portrait_offset_x", 0)
            pokemon_portrait_offset_y = global_offsets.get("pokemon_portrait_offset_y", 0)
            
            print(f"🎯 Global offsets (for JSON only): Sprite: X={pokemon_sprite_offset_x}, Y={pokemon_sprite_offset_y}, Portrait: X={pokemon_portrait_offset_x}, Y={pokemon_portrait_offset_y}")
            
            total_frames = 0
            frame_mapping = {}
            frame_reuse_map = {}  # Map to track frame reuse
            
            used_frames_per_animation = {}

            # First pass: identify frame reuse opportunities
            for stardew_anim in anim_set.stardew_animations:
                pokemon_anim = next((a for a in anim_set.animations if a.name == stardew_anim.pokemon_anim_name), None)
                if not pokemon_anim:
                    continue
                    
                # Check if this animation can reuse frames from another Stardew animation
                can_reuse = False
                reuse_source_anim = None
                
                for existing_anim_name, existing_data in frame_mapping.items():
                    existing_stardew_anim = next((sa for sa in anim_set.stardew_animations if sa.stardew_anim_name == existing_anim_name), None)
                    if (existing_stardew_anim and 
                        existing_stardew_anim.pokemon_anim_name == stardew_anim.pokemon_anim_name and
                        existing_stardew_anim.stardew_map.mode == stardew_anim.stardew_map.mode and
                        existing_stardew_anim.stardew_map.use_front_only == stardew_anim.stardew_map.use_front_only):
                        
                        # Check if frame indices match for all directions
                        directions_match = True
                        for direction in ['front', 'right', 'back', 'left']:
                            existing_frames = getattr(existing_stardew_anim, f'pokemon_frames_index_{direction}')
                            current_frames = getattr(stardew_anim, f'pokemon_frames_index_{direction}')
                            if existing_frames != current_frames:
                                directions_match = False
                                break
                        
                        if directions_match:
                            can_reuse = True
                            reuse_source_anim = existing_anim_name
                            break
                
                if can_reuse and reuse_source_anim:
                    # Reuse frames from existing animation
                    frame_mapping[stardew_anim.stardew_anim_name] = {
                        'start_index': frame_mapping[reuse_source_anim]['start_index'],
                        'frame_count': frame_mapping[reuse_source_anim]['frame_count'],
                        'front_frames': stardew_anim.pokemon_frames_index_front,
                        'right_frames': stardew_anim.pokemon_frames_index_right,
                        'back_frames': stardew_anim.pokemon_frames_index_back,
                        'left_frames': stardew_anim.pokemon_frames_index_left,
                        'flip_left': stardew_anim.stardew_map.flip_left_frames,
                        'use_front_only': stardew_anim.stardew_map.use_front_only,
                        'duration_mult': stardew_anim.stardew_map.duration_mult,
                        'conditions_names': stardew_anim.stardew_map.conditions_names,
                        'conditions_group_names': stardew_anim.stardew_map.conditions_group_names,
                        'body_type': stardew_anim.stardew_map.body_type.value,
                        'mode': stardew_anim.stardew_map.mode.value,
                        'offset_x': offset_x,
                        'offset_y': offset_y,
                        'reuses_frames_from': reuse_source_anim
                    }
                    print(f"🔄 {stardew_anim.stardew_anim_name} reuses frames from {reuse_source_anim}")
                    continue

                # Calculate frame count for new animation
                anim_frames = (
                    len(stardew_anim.pokemon_frames_index_front) +
                    len(stardew_anim.pokemon_frames_index_right) +
                    len(stardew_anim.pokemon_frames_index_back) +
                    len(stardew_anim.pokemon_frames_index_left)
                )
                
                if anim_frames > 0:
                    frame_mapping[stardew_anim.stardew_anim_name] = {
                        'start_index': total_frames,
                        'frame_count': anim_frames,
                        'front_frames': stardew_anim.pokemon_frames_index_front,
                        'right_frames': stardew_anim.pokemon_frames_index_right,
                        'back_frames': stardew_anim.pokemon_frames_index_back,
                        'left_frames': stardew_anim.pokemon_frames_index_left,
                        'flip_left': stardew_anim.stardew_map.flip_left_frames,
                        'use_front_only': stardew_anim.stardew_map.use_front_only,
                        'duration_mult': stardew_anim.stardew_map.duration_mult,
                        'conditions_names': stardew_anim.stardew_map.conditions_names,
                        'conditions_group_names': stardew_anim.stardew_map.conditions_group_names,
                        'body_type': stardew_anim.stardew_map.body_type.value,
                        'mode': stardew_anim.stardew_map.mode.value,
                        'offset_x': offset_x,
                        'offset_y': offset_y,
                        'reuses_frames_from': None
                    }
                    total_frames += anim_frames
                    
                    if debug_frames:
                        all_used_frames = (
                            stardew_anim.pokemon_frames_index_front +
                            stardew_anim.pokemon_frames_index_right +
                            stardew_anim.pokemon_frames_index_back +
                            stardew_anim.pokemon_frames_index_left
                        )
                        used_frames_per_animation[pokemon_anim.name] = all_used_frames
            
            if total_frames == 0:
                print(f"⚠️ No frames to generate for {anim_set.variant_name}")
                continue
                
            if debug_frames:
                print(f"🛠️ Generating debug spritesheets for {anim_set.variant_name}...")
                for anim in anim_set.animations:
                    if anim.name in used_frames_per_animation:
                        debug_sprite = create_debug_spritesheet(
                            anim, 
                            anim_set.directory, 
                            used_frames_per_animation[anim.name]
                        )
                        if debug_sprite:
                            debug_filename = f"DEBUG_{anim.anim_path}"
                            debug_path = os.path.join(output_dir, debug_filename)
                            debug_sprite.save(debug_path, 'PNG')
                            print(f"✅ Generated debug spritesheet: {debug_path}")
                
            rows_needed = (total_frames + frames_per_row - 1) // frames_per_row
            spritesheet_width = anim_set.max_width * frames_per_row
            spritesheet_height = anim_set.max_height * rows_needed
            
            spritesheet = Image.new('RGBA', (spritesheet_width, spritesheet_height), (0, 0, 0, 0))
            
            variant_frame_mapping = {}
            current_frame_index = 0
            processed_animations = set()  # Track animations we've processed
        

            for stardew_anim in anim_set.stardew_animations:
                if stardew_anim.stardew_anim_name not in frame_mapping:
                    continue
                    
                anim_data = frame_mapping[stardew_anim.stardew_anim_name]
                
                # Skip if this animation reuses frames (already processed)
                if anim_data.get('reuses_frames_from'):
                    print(f"⏭️ Skipping frame copy for {stardew_anim.stardew_anim_name} (reuses {anim_data['reuses_frames_from']})")
                    continue
                    
                pokemon_anim = next((a for a in anim_set.animations if a.name == stardew_anim.pokemon_anim_name), None)
                if not pokemon_anim:
                    continue
                    
                pokemon_sprite_path = os.path.join(anim_set.directory, pokemon_anim.anim_path)
                if not os.path.exists(pokemon_sprite_path):
                    print(f"⚠️ Missing sprite: {pokemon_sprite_path}")
                    continue
                    
                try:
                    pokemon_sprite = Image.open(pokemon_sprite_path).convert('RGBA')
                except Exception as e:
                    print(f"⚠️ Failed to load {pokemon_sprite_path}: {e}")
                    continue
                
                anim_color = stardew_anim.stardew_map.debug_font_color
                
                directions = [
                    ('front', stardew_anim.pokemon_frames_index_front, False),
                    ('right', stardew_anim.pokemon_frames_index_right, False),
                    ('back', stardew_anim.pokemon_frames_index_back, False),
                    ('left', stardew_anim.pokemon_frames_index_left, stardew_anim.stardew_map.flip_left_frames)
                ]
                
                for direction_name, frame_indices, should_flip in directions:
                    for pokemon_frame_index in frame_indices:
                        frames_per_direction = pokemon_anim.total_frames
                        row = pokemon_frame_index // frames_per_direction
                        col = pokemon_frame_index % frames_per_direction
                        
                        x1 = col * pokemon_anim.frame_width
                        y1 = row * pokemon_anim.frame_height
                        x2 = x1 + pokemon_anim.frame_width
                        y2 = y1 + pokemon_anim.frame_height
                        
                        if (x2 > pokemon_sprite.width or y2 > pokemon_sprite.height):
                            print(f"⚠️ Frame {pokemon_frame_index} out of bounds in {pokemon_sprite_path}: ({x1},{y1})-({x2},{y2}) vs sprite size {pokemon_sprite.size}")
                            continue
                        
                        try:
                            frame = pokemon_sprite.crop((x1, y1, x2, y2))
                            
                            if should_flip:
                                frame = ImageOps.mirror(frame)
                            
                            output_col = current_frame_index % frames_per_row
                            output_row = current_frame_index // frames_per_row
                            
                            output_x = output_col * anim_set.max_width
                            output_y = output_row * anim_set.max_height
                            
                            final_frame = Image.new('RGBA', (anim_set.max_width, anim_set.max_height), (0, 0, 0, 0))
                            
                            offset_x_center = (anim_set.max_width - pokemon_anim.frame_width) // 2
                            offset_y_center = ((anim_set.max_height - pokemon_anim.frame_height) // 2) + foot_difference
                            
                            final_frame.paste(frame, (offset_x_center, offset_y_center), frame)
                            
                            spritesheet.paste(final_frame, (output_x, output_y))
                            
                            variant_frame_mapping[current_frame_index] = pokemon_frame_index

                            current_frame_index += 1
                            
                        except Exception as e:
                            print(f"⚠️ Error processing frame {pokemon_frame_index} for {anim_set.variant_name}: {e}")
                            continue
                    
            frame_mapping_data[anim_set.variant_name] = variant_frame_mapping
            output_path = os.path.join(output_dir, "body.png")
            spritesheet.save(output_path, 'PNG')
            
            # Calculate actual reused frames count
            reused_animations = [anim_name for anim_name, data in frame_mapping.items() if data.get('reuses_frames_from')]
            original_frame_count = sum(data['frame_count'] for data in frame_mapping.values() if not data.get('reuses_frames_from'))
            optimized_frame_count = total_frames
            
            if variations_as_subfolders:
                if is_base_variant:
                    print(f"🏠 Generated (base): {output_path} ({spritesheet_width}x{spritesheet_height}) - {optimized_frame_count} frames (saved {original_frame_count - optimized_frame_count} frames) - JSON Offset: X={offset_x}, Y={offset_y}")
                else:
                    print(f"📁 Generated (variant): {output_path} ({spritesheet_width}x{spritesheet_height}) - {optimized_frame_count} frames (saved {original_frame_count - optimized_frame_count} frames) - JSON Offset: X={offset_x}, Y={offset_y}")
            else:
                print(f"📄 Generated: {output_path} ({spritesheet_width}x{spritesheet_height}) - {optimized_frame_count} frames (saved {original_frame_count - optimized_frame_count} frames) - JSON Offset: X={offset_x}, Y={offset_y}")
            
            if reused_animations:
                print(f"🔄 Reused frames for: {', '.join(reused_animations)}")
            
            spritesheet_data = {
                'directory': output_dir,
                'max_width': anim_set.max_width,
                'max_height': anim_set.max_height,
                'frames_per_row': frames_per_row,
                'total_frames': total_frames,
                'animation_mapping': frame_mapping,
                'pokemon_id': anim_set.pokemon_id,
                'pokemon_name': anim_set.pokemon_name,
                'generation': anim_set.generation,
                'offset_x': offset_x,
                'offset_y': offset_y,
                'global_offsets': global_offsets,
                'variation_type': variation_type
            }
            
            spritesheet_mapping[anim_set.variant_name] = spritesheet_data
            
            try:
                generate_body_json(anim_set, spritesheet_data, output_dir)
            except Exception as e:
                print(f"⚠️ Failed to generate body.json for {anim_set.variant_name}: {e}")
    
    for variant_name, sprite_data in spritesheet_mapping.items():
        sprite_data['frame_mapping'] = frame_mapping_data.get(variant_name, {})

    print(f"✅ Generated {len(spritesheet_mapping)} spritesheets and body.json files")
    return spritesheet_mapping

def create_debug_spritesheet(animation: AnimationData, directory: str, used_frames: List[int]):
    """Create a debug version of the spritesheet with numbered frames"""
    sprite_path = os.path.join(directory, animation.anim_path)
    if not os.path.exists(sprite_path):
        return None
    
    try:
        from PIL import Image
        original_sprite = Image.open(sprite_path).convert('RGBA')
        debug_sprite = original_sprite.copy()
        
        font = load_pixel_font()
        
        frame_width = animation.frame_width
        frame_height = animation.frame_height
        frames_per_row = debug_sprite.width // frame_width
        total_rows = debug_sprite.height // frame_height
        
        frame_count = 0
        
        for row in range(total_rows):
            for col in range(frames_per_row):
                if frame_count >= animation.total_frames * 8:
                    break
                    
                x1 = col * frame_width
                y1 = row * frame_height
                x2 = x1 + frame_width
                y2 = y1 + frame_height
                
                if frame_count in used_frames:
                    original_frame = original_sprite.crop((x1, y1, x2, y2))

                    background = Image.new('RGBA', (frame_width, frame_height), DEBUG_CONFIG['background_color'])
                    
                    combined_frame = Image.alpha_composite(background, original_frame)
                    
                    debug_sprite.paste(combined_frame, (x1, y1))
                
                frame_image = debug_sprite.crop((x1, y1, x2, y2))
                frame_draw = ImageDraw.Draw(frame_image)
                text = str(frame_count)
                draw_debug_text(frame_draw, frame_width, frame_height, text, font, DEBUG_CONFIG['pokemon_text_align'], DEBUG_CONFIG['pokemon_font_color'], DEBUG_CONFIG['pokemon_font_background_color'], DEBUG_CONFIG['pokemon_offset_size'])
                
                debug_sprite.paste(frame_image, (x1, y1))
                
                frame_count += 1

        return debug_sprite
        
    except Exception as e:
        print(f"⚠️ Error creating debug spritesheet for {animation.anim_path}: {e}")
        return None
    
def add_debug_numbers_to_spritesheet(spritesheet_path: str, frame_width: int, frame_height: int, 
                                   total_frames: int, frames_per_row: int, frame_mapping: dict):
    """Add debug numbers to spritesheet after all optimizations are complete"""
    print(f"🔢 Adding debug numbers to: {spritesheet_path}")
    
    try:
        with Image.open(spritesheet_path) as spritesheet:
            spritesheet = spritesheet.convert('RGBA')
            debug_font = load_pixel_font()
            
            if not debug_font:
                print("⚠️ Could not load debug font, skipping debug numbers")
                return
            
            # Create a copy to draw on
            debug_sheet = spritesheet.copy()
            
            for frame_index in range(total_frames):
                row = frame_index // frames_per_row
                col = frame_index % frames_per_row
                
                x_start = col * frame_width
                y_start = row * frame_height
                
                # Extract the individual frame
                frame_box = (x_start, y_start, x_start + frame_width, y_start + frame_height)
                frame = debug_sheet.crop(frame_box)
                frame_draw = ImageDraw.Draw(frame)
                
                # Get Pokémon frame number from mapping
                pokemon_frame_index = frame_mapping.get(frame_index, -1)
                
                # Draw Stardew frame number (top left)
                stardew_text = f"{frame_index}"
                draw_debug_text(frame_draw, frame_width, frame_height, stardew_text, debug_font, 
                              'top_left', DEBUG_CONFIG['stardew_font_color'], 
                              DEBUG_CONFIG['stardew_font_background_color'], DEBUG_CONFIG['stardew_offset_size'])
                
                # Draw Pokémon frame number (bottom left)
                if pokemon_frame_index != -1:
                    pokemon_text = f"{pokemon_frame_index}"
                    draw_debug_text(frame_draw, frame_width, frame_height, pokemon_text, debug_font, 
                                  'bottom_left', DEBUG_CONFIG['pokemon_font_color'], 
                                  DEBUG_CONFIG['pokemon_font_background_color'], DEBUG_CONFIG['pokemon_offset_size'])
                else:
                    pokemon_text = "?"
                    draw_debug_text(frame_draw, frame_width, frame_height, pokemon_text, debug_font, 
                                  'bottom_left', (255, 100, 100, 192),  # Red for missing mapping
                                  DEBUG_CONFIG['pokemon_font_background_color'], DEBUG_CONFIG['pokemon_offset_size'])
                
                # Paste the modified frame back
                debug_sheet.paste(frame, frame_box)
                
            # Save debug version
            debug_sheet.save(spritesheet_path, 'PNG')
            print(f"✅ Debug numbers added to: {spritesheet_path}")
            
    except Exception as e:
        print(f"❌ Error adding debug numbers: {e}")
