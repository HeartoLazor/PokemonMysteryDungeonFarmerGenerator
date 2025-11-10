# Author: HeartoLazor
# Description: JSON template processing and body.json generation

import os
from data_models.animation_models import AnimationSet
from typing import Dict
from data_models.enums import StardewBodyModelType, StardewAnimationDataModes
from config.settings import app_settings
from .template_loader import load_template

def get_json_frame_sequence(stardew_anim, base_idx, frames_count):
    """Get frame sequence for JSON generation (applies mode-specific rules)"""
    mode = stardew_anim.stardew_map.mode
    
    if mode == StardewAnimationDataModes.default:
        return list(range(base_idx, base_idx + frames_count))
        
    elif mode == StardewAnimationDataModes.force_frame:
        frame_idx = min(stardew_anim.stardew_map.frame, frames_count - 1)
        return [base_idx + frame_idx]
        
    elif mode == StardewAnimationDataModes.range_start_end:
        start = min(stardew_anim.stardew_map.frame_start, frames_count - 1)
        end = min(stardew_anim.stardew_map.frame_end, frames_count - 1)
        return list(range(base_idx + start, base_idx + end + 1))
        
    elif mode == StardewAnimationDataModes.range_start_negative_end:
        frames = []
        
        # Process frame_range_start (positive indices)
        for start_val in stardew_anim.stardew_map.frame_range_start:
            if 0 <= start_val < frames_count:
                frames.append(base_idx + start_val)
        
        # Process frame_range_end (can be negative indices)
        for end_val in stardew_anim.stardew_map.frame_range_end:
            if end_val < 0:
                # Convert negative index to positive: -1 means last frame, -2 means second last, etc.
                positive_idx = frames_count + end_val
                if 0 <= positive_idx < frames_count:
                    frames.append(base_idx + positive_idx)
            else:
                # Positive index
                if 0 <= end_val < frames_count:
                    frames.append(base_idx + end_val)
        
        # Remove duplicates and sort
        frames = sorted(list(set(frames)))
        return frames
        
    elif mode == StardewAnimationDataModes.portrait:
        frame_idx = min(stardew_anim.stardew_map.frame, frames_count - 1)
        return [base_idx + frame_idx]
        
    elif mode == StardewAnimationDataModes.repeat_frame_count:
        # Get the base frames (all frames from this direction)
        base_frames = list(range(base_idx, base_idx + frames_count))
        
        # Repeat the sequence until we reach frame_quantity
        repeated_frames = []
        for i in range(stardew_anim.stardew_map.frame_quantity):
            frame_index = i % len(base_frames)
            repeated_frames.append(base_frames[frame_index])
        
        return repeated_frames
            
    return []

def generate_single_frame_data(stardew_anim, pokemon_anim, pokemon_frame_idx, body_frame_number, 
                              frame_offset_x, frame_offset_y, frame_template, condition_template,
                              pokemon_sprite_offset_x, pokemon_sprite_offset_y):
    """Helper function to generate frame data for JSON"""
    frames_per_direction = pokemon_anim.total_frames
    original_frame_row = pokemon_frame_idx // frames_per_direction
    original_frame_col = pokemon_frame_idx % frames_per_direction
    
    duration = 100
    if original_frame_col < len(pokemon_anim.durations):
        duration = int(round(pokemon_anim.durations[original_frame_col] * stardew_anim.stardew_map.duration_mult, 0))
    
    conditions_data = []
    for condition_name in stardew_anim.stardew_map.conditions_names:
        condition_data = condition_template.replace("{{condition_type}}", "Name")
        condition_data = condition_data.replace("{{condition_name}}", condition_name)
        conditions_data.append(condition_data)
    
    for group_name in stardew_anim.stardew_map.conditions_group_names:
        condition_data = condition_template.replace("{{condition_type}}", "GroupName")
        condition_data = condition_data.replace("{{condition_name}}", group_name)
        conditions_data.append(condition_data)
    
    if conditions_data:
        conditions_str = ",\n".join(conditions_data)
    else:
        conditions_str = ""
    
    final_offset_x = frame_offset_x + pokemon_sprite_offset_x + stardew_anim.stardew_map.sprite_offset_x
    final_offset_y = frame_offset_y + pokemon_sprite_offset_y + stardew_anim.stardew_map.sprite_offset_y
    
    frame_data = frame_template.replace("{{body_frame_number}}", str(body_frame_number))
    frame_data = frame_data.replace("{{stardew_animation_name}}", stardew_anim.stardew_anim_name)
    frame_data = frame_data.replace("{{pokemon_frame_number}}", str(pokemon_frame_idx))
    frame_data = frame_data.replace("{{pokemon_animation_name}}", pokemon_anim.anim_path)
    frame_data = frame_data.replace("{{duration}}", str(int(duration)))
    frame_data = frame_data.replace("{{end_when_farmer_frame_updates}}", str(stardew_anim.stardew_map.end_when_farmer_frame_updates).lower())
    frame_data = frame_data.replace("{{ingame_frame_offset_x}}", str(final_offset_x))
    frame_data = frame_data.replace("{{ingame_frame_offset_y}}", str(final_offset_y))
    frame_data = frame_data.replace("{{conditions}}", conditions_str)
    
    return frame_data

def generate_body_json(anim_set: AnimationSet, spritesheet_data: Dict, output_dir: str):
    print(f"🛠️ Generating body.json for {anim_set.variant_name}")
    
    try:
        body_template = load_template("body.template")
        body_type_template = load_template("body_type.template")
        animation_template = load_template("animation.template")
        frame_template = load_template("frame.template")
        condition_template = load_template("condition.template")
        portrait_template = load_template("portrait.template")
        
        print(f"✅ All templates loaded successfully")
        
        offset_x = spritesheet_data.get('offset_x', 0)
        offset_y = spritesheet_data.get('offset_y', 0)
        
        global_offsets = spritesheet_data.get('global_offsets', {})
        pokemon_sprite_offset_x = global_offsets.get("pokemon_sprite_offset_x", 0)
        pokemon_sprite_offset_y = global_offsets.get("pokemon_sprite_offset_y", 0)
        pokemon_portrait_offset_x = global_offsets.get("pokemon_portrait_offset_x", 0)
        pokemon_portrait_offset_y = global_offsets.get("pokemon_portrait_offset_y", 0)
        
        accessory_offset = global_offsets.get("accessory_offset", 0)
        head_offset = global_offsets.get("head_offset", -4)
        leg_offset = global_offsets.get("leg_offset", 0)
        shoe_offset = global_offsets.get("shoe_offset", 0)
        body_offset = global_offsets.get("body_offset", 0)
        arms_offset = global_offsets.get("arms_offset", 0)
        
        print(f"📐 Using calculated offsets: X={offset_x}, Y={offset_y}")
        print(f"🎯 Global offsets - Sprite: X={pokemon_sprite_offset_x}, Y={pokemon_sprite_offset_y}, Portrait: X={pokemon_portrait_offset_x}, Y={pokemon_portrait_offset_y}")
        print(f"🎯 Body template offsets - Accessory:{accessory_offset}, Head:{head_offset}, Leg:{leg_offset}, Shoe:{shoe_offset}, Body:{body_offset}, Arms:{arms_offset}")
        
        is_alternative = any(char.isdigit() for char in anim_set.variant_name.split(app_settings.NAME_SEPARATOR)[-1])
        alternative_tag = "Alternative" if is_alternative else ""
        
        is_custom = anim_set.pokemon_id == "-1"
        custom_tag = "Custom" if is_custom else ""
        
        if is_custom:
            gen_number = "Custom"
        else:
            gen_number = "".join(filter(str.isdigit, anim_set.generation)) or "1"
        
        print(f"📊 Variant info: name={anim_set.variant_name}, alternative={is_alternative}, custom={is_custom}, gen={gen_number}")
        
        portrait_anim = None
        for stardew_anim in anim_set.stardew_animations:
            if stardew_anim.stardew_anim_name == "portrait":
                portrait_anim = stardew_anim
                break
        
        body_types_data = {}
        directions = [
            ("front", "FrontBody", False),
            ("right", "RightBody", False), 
            ("back", "BackBody", False),
            ("left", "LeftBody", True)
        ]
        
        # Get animation mapping from spritesheet data
        animation_mapping = spritesheet_data.get('animation_mapping', {})
        
        for direction, body_type_name, flipped in directions:
            print(f"🔧 Processing {body_type_name} direction...")
            
            has_animations = any(
                len(getattr(stardew_anim, f"pokemon_frames_index_{direction}")) > 0
                for stardew_anim in anim_set.stardew_animations
            )
            
            if not has_animations:
                print(f"⚠️ No animations for {body_type_name}, skipping")
                body_types_data[body_type_name.lower()] = ""
                continue
            
            idle_animations = []
            movement_animations = []
            
            for stardew_anim in anim_set.stardew_animations:
                # Get the actual frame indices from the spritesheet (what's physically there)
                actual_frame_indices = getattr(stardew_anim, f"pokemon_frames_index_{direction}")
                if not actual_frame_indices:
                    continue
                
                print(f"  🎬 Processing {stardew_anim.stardew_anim_name} with {len(actual_frame_indices)} actual frames (mode: {stardew_anim.stardew_map.mode.name})")
                
                pokemon_anim = next((a for a in anim_set.animations if a.name == stardew_anim.pokemon_anim_name), None)
                if not pokemon_anim:
                    print(f"  ⚠️ Pokémon animation {stardew_anim.pokemon_anim_name} not found")
                    continue
                
                # Get the correct start index from animation mapping (handles frame reuse)
                anim_mapping_data = animation_mapping.get(stardew_anim.stardew_anim_name, {})
                actual_start_index = anim_mapping_data.get('start_index', 0)
                
                frames_data = []
                
                # Calculate frames before this direction in the ACTUAL spritesheet for THIS animation
                frames_before_this_direction = 0
                direction_order = ["front", "right", "back", "left"]
                current_direction_index = direction_order.index(direction)

                # Only count frames from previous directions for this specific animation
                for prev_direction in direction_order[:current_direction_index]:
                    prev_frames = getattr(stardew_anim, f"pokemon_frames_index_{prev_direction}")
                    frames_before_this_direction += len(prev_frames)

                # Get the correct start index from animation mapping (handles frame reuse)
                anim_mapping_data = animation_mapping.get(stardew_anim.stardew_anim_name, {})
                actual_start_index = anim_mapping_data.get('start_index', 0)

                # Calculate base index for this direction
                frames_per_direction = pokemon_anim.total_frames
                base_idx = {"front": 0, "right": frames_per_direction * 2, "back": frames_per_direction * 4, "left": frames_per_direction * 6}.get(direction, 0)

                # Get the JSON frame sequence (applies mode-specific rules)
                json_frame_sequence = get_json_frame_sequence(stardew_anim, base_idx, frames_per_direction)

                # Calculate the starting frame for THIS direction in the spritesheet
                # This is based on the ACTUAL frames in the spritesheet, not the JSON sequence
                current_stardew_frame = actual_start_index + frames_before_this_direction

                # Map JSON frame sequence to actual sprite indices
                json_frames_data = []

                # Calculate how many unique frames we have in the actual spritesheet for this direction
                unique_frames_count = len(actual_frame_indices)

                for i, json_frame_idx in enumerate(json_frame_sequence):
                    # Convert JSON frame index to actual sprite index
                    # The JSON frame index is relative to the base_idx for this direction
                    relative_frame_idx = json_frame_idx - base_idx
                    
                    # Ensure the relative frame index is within bounds of actual frames
                    if 0 <= relative_frame_idx < unique_frames_count:
                        actual_sprite_idx = actual_frame_indices[relative_frame_idx]
                        
                        # For ALL modes, use the actual frame number from the spritesheet
                        # Don't create new frame numbers - reuse what's already in the spritesheet
                        actual_body_frame = actual_start_index + frames_before_this_direction + relative_frame_idx
                        
                        frame_data = generate_single_frame_data(
                            stardew_anim, pokemon_anim, actual_sprite_idx, 
                            actual_body_frame, offset_x, offset_y,
                            frame_template, condition_template,
                            pokemon_sprite_offset_x, pokemon_sprite_offset_y
                        )
                        json_frames_data.append(frame_data)

                # Handle mode-specific frame counting
                if stardew_anim.stardew_map.mode == StardewAnimationDataModes.repeat_frame_count:
                    # For repeat mode, we might need to repeat the frames in the data array
                    # but we're already reusing the same frame numbers
                    frame_quantity = stardew_anim.stardew_map.frame_quantity
                    if len(json_frames_data) < frame_quantity:
                        # Repeat the existing frames to reach the desired quantity
                        original_frames = json_frames_data.copy()
                        json_frames_data = []
                        for i in range(frame_quantity):
                            frame_index = i % len(original_frames)
                            json_frames_data.append(original_frames[frame_index])
                    
                    print(f"  🔄 {stardew_anim.stardew_anim_name}: Reused {unique_frames_count} frames for {len(json_frames_data)} JSON entries")

                # For ALL modes, we DON'T advance current_stardew_frame because we're reusing existing frames
                # The spritesheet already contains all the frames we need
                frames_data.extend(json_frames_data)

                print(f"  📋 {stardew_anim.stardew_anim_name}: Generated {len(json_frames_data)} JSON frames reusing {unique_frames_count} sprite frames")

                frames_joined = ",\n".join(frames_data)
                animation_data = animation_template.replace("{{frames}}", frames_joined)
                
                if stardew_anim.stardew_map.body_type == StardewBodyModelType.idle_animation:
                    idle_animations.append(animation_data)
                elif stardew_anim.stardew_map.body_type == StardewBodyModelType.movement_animation:
                    movement_animations.append(animation_data)
            
            portrait_data = ""
            if direction == "front" and portrait_anim:
                print(f"  🖼️ Generating portrait for front body")
                portrait_frames = portrait_anim.pokemon_frames_index_front
                if portrait_frames:
                    pokemon_frame_idx = portrait_frames[0]
                    pokemon_anim = next((a for a in anim_set.animations if a.name == portrait_anim.pokemon_anim_name), None)
                    if pokemon_anim:
                        frames_per_direction = pokemon_anim.total_frames
                        row = pokemon_frame_idx // frames_per_direction
                        col = pokemon_frame_idx % frames_per_direction
                        
                        portrait_offset_x = portrait_anim.stardew_map.portrait_offset_x + pokemon_portrait_offset_x
                        portrait_offset_y = portrait_anim.stardew_map.portrait_offset_y + pokemon_portrait_offset_y
                        
                        portrait_data = portrait_template.replace("{{portrait_x}}", str(col * pokemon_anim.frame_width))
                        portrait_data = portrait_data.replace("{{portrait_y}}", str(row * pokemon_anim.frame_height))
                        portrait_data = portrait_data.replace("{{max_width}}", str(anim_set.max_width))
                        portrait_data = portrait_data.replace("{{max_height}}", str(anim_set.max_height))
                        portrait_data = portrait_data.replace("{{ingame_portrait_offset_x}}", str(-anim_set.max_width + portrait_offset_x))
                        portrait_data = portrait_data.replace("{{ingame_portrait_offset_y}}", str(-(anim_set.max_height + offset_y) + portrait_offset_y))
                        print(f"  ✅ Portrait data generated with offsets X:{portrait_offset_x}, Y:{portrait_offset_y}")
            
            body_type_data = body_type_template.replace("{{body_type}}", body_type_name)
            body_type_data = body_type_data.replace("{{flipped}}", str(flipped).lower())
            body_type_data = body_type_data.replace("{{max_width}}", str(anim_set.max_width))
            body_type_data = body_type_data.replace("{{max_height}}", str(anim_set.max_height))
            body_type_data = body_type_data.replace("{{accessory_offset}}", str(accessory_offset))
            body_type_data = body_type_data.replace("{{head_offset}}", str(head_offset))
            body_type_data = body_type_data.replace("{{leg_offset}}", str(leg_offset))
            body_type_data = body_type_data.replace("{{shoe_offset}}", str(shoe_offset))
            body_type_data = body_type_data.replace("{{body_offset}}", str(body_offset))
            body_type_data = body_type_data.replace("{{arms_offset}}", str(arms_offset))
            body_type_data = body_type_data.replace("{{portrait}}", portrait_data)
            body_type_data = body_type_data.replace("{{idle_animations}}", ",\n".join(idle_animations) if idle_animations else "")
            body_type_data = body_type_data.replace("{{movement_animations}}", ",\n".join(movement_animations) if movement_animations else "")
            
            body_types_data[body_type_name.lower()] = body_type_data
            print(f"  ✅ {body_type_name} completed with {len(idle_animations)} idle, {len(movement_animations)} movement animations")
        
        tags = [
            '"Pokemon"',
        ]
            
        if custom_tag:
            tags.append(f'"{anim_set.pokemon_name}"')
            tags.append(f'"{custom_tag}"')
        else:
            tags.append(f'"Gen {gen_number}"')
            tags.append(f'"{anim_set.pokemon_id}"')
            tags.append(f'"{anim_set.pokemon_name}"')
        
        if alternative_tag:
            tags.append(f'"{alternative_tag}"')
        
        variation_type = spritesheet_data.get('variation_type')
        if variation_type:
            tags.append(f'"{variation_type}"')
            print(f"   Added variation type tag: {variation_type}")

        tags_str = "    " + ",\n    ".join(tags)

        body_json = body_template.replace("{{pokemon_id_name}}", anim_set.variant_name)
        body_json = body_json.replace("{{pokemon_tags}}", tags_str)
        body_json = body_json.replace("{{front_body_type}}", body_types_data.get("frontbody", ""))
        body_json = body_json.replace("{{right_body_type}}", body_types_data.get("rightbody", ""))
        body_json = body_json.replace("{{back_body_type}}", body_types_data.get("backbody", ""))
        body_json = body_json.replace("{{left_body_type}}", body_types_data.get("leftbody", ""))
        
        output_path = os.path.join(output_dir, "body.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(body_json)
        
        print(f"✅ Generated body.json: {output_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate body.json for {anim_set.variant_name}: {e}")
        import traceback
        traceback.print_exc()