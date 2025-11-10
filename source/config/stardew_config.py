# Author: HeartoLazor
# Description: Stardew Valley animation configuration loader

import json
import os
from data_models.animation_models import (
    StardewAnimationDefault, 
    StardewAnimationForceFrame, StardewAnimationPortrait,
    StardewAnimationRangeStartEnd, StardewAnimationRangeStartNegativeEnd,
    StardewAnimationRepeatFrameCount
)
from data_models.enums import StardewAnimationDataModes, StardewBodyModelType
from config.settings import app_settings

def load_stardew_mapping_config(pokemon_id: str = None, pokemon_name: str = None, is_custom: bool = False) -> tuple:
    config_dir = app_settings.CONFIG_DIR
    default_config_path = os.path.join(config_dir, "default_config.json")
    
    if not os.path.exists(default_config_path):
        raise FileNotFoundError(f"Default configuration file not found: {default_config_path}")
    
    try:
        with open(default_config_path, 'r', encoding='utf-8') as f:
            default_config_data = json.load(f)
        print(f"✅ Loaded default config: {default_config_path}")
    except Exception as e:
        print(f"❌ Failed to load default config {default_config_path}: {e}")
        raise
    
    config_data = default_config_data.copy()
    
    config_loaded = False
    if pokemon_id and not is_custom:
        pokemon_config_path = os.path.join(config_dir, f"{pokemon_id}.json")
        if os.path.exists(pokemon_config_path):
            try:
                with open(pokemon_config_path, 'r', encoding='utf-8') as f:
                    pokemon_config_data = json.load(f)
                
                print(f"✅ Loaded Pokémon-specific config: {pokemon_config_path}")
                config_loaded = True
                
                if "global_offsets" in pokemon_config_data:
                    merged_global_offsets = config_data.get("global_offsets", {}).copy()
                    merged_global_offsets.update(pokemon_config_data["global_offsets"])
                    config_data["global_offsets"] = merged_global_offsets
                    print(f"🔄 Merged global_offsets: {merged_global_offsets}")
                
                if "animations" in pokemon_config_data:
                    config_data["animations"] = pokemon_config_data["animations"]
                    print(f"🔄 Using Pokémon-specific animations list ({len(config_data['animations'])} animations)")
                
            except Exception as e:
                print(f"⚠️ Failed to load Pokémon config {pokemon_config_path}: {e}")
    
    if (is_custom and pokemon_name) or (not config_loaded and pokemon_name):
        config_name = pokemon_name
        pokemon_config_path = os.path.join(config_dir, f"{config_name}.json")
        if os.path.exists(pokemon_config_path):
            try:
                with open(pokemon_config_path, 'r', encoding='utf-8') as f:
                    pokemon_config_data = json.load(f)
                
                config_type = "custom" if is_custom else "name-based"
                print(f"✅ Loaded {config_type} config: {pokemon_config_path}")
                config_loaded = True
                
                if "global_offsets" in pokemon_config_data:
                    merged_global_offsets = config_data.get("global_offsets", {}).copy()
                    merged_global_offsets.update(pokemon_config_data["global_offsets"])
                    config_data["global_offsets"] = merged_global_offsets
                    print(f"🔄 Merged global_offsets: {merged_global_offsets}")
                
                if "animations" in pokemon_config_data:
                    config_data["animations"] = pokemon_config_data["animations"]
                    print(f"🔄 Using {config_type} animations list ({len(config_data['animations'])} animations)")
                
            except Exception as e:
                print(f"⚠️ Failed to load {config_type} config {pokemon_config_path}: {e}")
    
    if not config_loaded:
        if is_custom:
            print(f"ℹ️ No custom config found for '{pokemon_name}', using default config")
        else:
            print(f"ℹ️ No Pokémon-specific config found for {pokemon_id}, using default config")
    
    global_offsets = config_data.get("global_offsets", {})
    
    default_global_offsets = {
        "pokemon_sprite_offset_x": 0,
        "pokemon_sprite_offset_y": 0,
        "pokemon_portrait_offset_x": 0,
        "pokemon_portrait_offset_y": 0,
        "accessory_offset": 0,
        "head_offset": -4,
        "leg_offset": 0,
        "shoe_offset": 0,
        "body_offset": 0,
        "arms_offset": 0
    }
    
    for key, default_value in default_global_offsets.items():
        if key not in global_offsets:
            global_offsets[key] = default_value
            print(f"🔧 Added missing global offset: {key} = {default_value}")
    
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
    
    global_offsets_dict = {
        "pokemon_sprite_offset_x": pokemon_sprite_offset_x,
        "pokemon_sprite_offset_y": pokemon_sprite_offset_y,
        "pokemon_portrait_offset_x": pokemon_portrait_offset_x,
        "pokemon_portrait_offset_y": pokemon_portrait_offset_y,
        "accessory_offset": accessory_offset,
        "head_offset": head_offset,
        "leg_offset": leg_offset,
        "shoe_offset": shoe_offset,
        "body_offset": body_offset,
        "arms_offset": arms_offset
    }
    
    stardew_mapping = []
    animation_configs = config_data.get("animations", [])
    
    for anim_config in animation_configs:
        anim_type = anim_config.get("type", "default")
        base_params = {
            "stardew_anim_name": anim_config["name"],
            "fallback_names": anim_config["fallback_names"],
            "use_front_only": anim_config.get("use_front_only", False),
            "flip_left_frames": anim_config.get("flip_left_frames", True),
            "duration_mult": anim_config.get("duration_mult", 1.0),
            "conditions_names": anim_config.get("conditions_names", []),
            "conditions_group_names": anim_config.get("conditions_group_names", []),
            "end_when_farmer_frame_updates": anim_config.get("end_when_farmer_frame_updates", False),
            "body_type": StardewBodyModelType[anim_config.get("body_type", "movement_animation")],
            "mode": StardewAnimationDataModes[anim_config.get("mode", "default")],
            "debug_font_color": tuple(anim_config.get("debug_font_color", [255, 255, 255, 192])),
            "discard_distance": anim_config.get("discard_distance", 0),
            "sprite_offset_x": anim_config.get("sprite_offset_x", 0),
            "sprite_offset_y": anim_config.get("sprite_offset_y", 0),
            "portrait_offset_x": anim_config.get("portrait_offset_x", 0),
            "portrait_offset_y": anim_config.get("portrait_offset_y", 0)
        }
        
        if anim_type == "portrait":
            stardew_mapping.append(StardewAnimationPortrait(
                frame=anim_config.get("frame", 0),
                **base_params
            ))
        elif anim_type == "force_frame":
            stardew_mapping.append(StardewAnimationForceFrame(
                frame=anim_config.get("frame", 0),
                **base_params
            ))
        elif anim_type == "range_start_end":
            stardew_mapping.append(StardewAnimationRangeStartEnd(
                frame_start=anim_config.get("frame_start", 0),
                frame_end=anim_config.get("frame_end", 0),
                **base_params
            ))
        elif anim_type == "range_start_negative_end":
            stardew_mapping.append(StardewAnimationRangeStartNegativeEnd(
                frame_range_start=anim_config.get("frame_range_start", []),
                frame_range_end=anim_config.get("frame_range_end", []),
                **base_params
            ))
        elif anim_type == "repeat_frame_count":
            stardew_mapping.append(StardewAnimationRepeatFrameCount(
                frame_quantity=anim_config.get("frame_quantity", 0),
                **base_params
            ))
        else:
            stardew_mapping.append(StardewAnimationDefault(**base_params))
    
    print(f"✅ Final configuration: {len(stardew_mapping)} animations")
    print(f"✅ Final global offsets: Sprite(X:{pokemon_sprite_offset_x}, Y:{pokemon_sprite_offset_y}), Portrait(X:{pokemon_portrait_offset_x}, Y:{pokemon_portrait_offset_y})")
    print(f"✅ Final body template offsets: Accessory:{accessory_offset}, Head:{head_offset}, Leg:{leg_offset}, Shoe:{shoe_offset}, Body:{body_offset}, Arms:{arms_offset}")
    
    return stardew_mapping, global_offsets_dict