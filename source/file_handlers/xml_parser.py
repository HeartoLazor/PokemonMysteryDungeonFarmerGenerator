# Author: HeartoLazor
# Description: Pokemon Mystery Dungeon AnimData.xml parser

import os
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from data_models.animation_models import AnimationData
from config.settings import app_settings

def get_variant_path_from_xml(xml_path: str, pokemon_base_dir: str) -> str:
    """Extract the variant path relative to Pokémon directory from XML path."""
    try:
        # Convert to absolute paths
        normalized_xml = Path(xml_path).resolve()
        
        # The pokemon_base_dir should be the Pokémon root directory, not the XML directory
        # Let's find the actual Pokémon root directory
        path_parts = normalized_xml.parts
        pokemon_index = None
        
        # Find the "pokemon" directory in the path
        for i, part in enumerate(path_parts):
            if part.lower() == "pokemon":
                pokemon_index = i
                break
        
        if pokemon_index is not None and pokemon_index + 1 < len(path_parts):
            # Reconstruct the Pokémon root directory path
            pokemon_root = Path(*path_parts[:pokemon_index + 2])  # Includes "pokemon" and Pokémon ID
            variant_parts = path_parts[pokemon_index + 2:-1]  # Parts after Pokémon ID, excluding filename
            
            print(f"🔍 DEBUG Path Calculation:")
            print(f"   XML Path: {normalized_xml}")
            print(f"   Pokémon Root: {pokemon_root}")
            print(f"   Variant Parts: {variant_parts}")
            
            # Construct variant path relative to Pokémon directory
            if variant_parts:
                variant_path = "/".join(variant_parts) + "/"
            else:
                variant_path = ""  # Base variant (no subfolder)
            
            # Preappend Pokémon ID for complete path
            pokemon_id = path_parts[pokemon_index + 1]
            full_variant_path = f"{pokemon_id}/{variant_path}"
            
            print(f"   Calculated Variant Path: '{full_variant_path}'")
            return full_variant_path
        else:
            print(f"❌ Could not find Pokémon directory in path: {normalized_xml}")
            return "./"
            
    except Exception as e:
        print(f"❌ Error calculating variant path: {e}")
        return "./"

def load_pokemon_names(csv_path: str):
    mapping = {}
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            num = row["number"].zfill(4)
            mapping[num] = {"name": row["name"], "generation": row["generation"]}
    return mapping

def find_animdata_files(base_dir: str, filter_list = None, custom_only: bool = False):
    anim_files = []
    
    search_dirs = []
    
    if not custom_only:
        search_dirs.append(os.path.join(base_dir, app_settings.POKEMON_SPRITES_SUB_DIRECTORY))
    
    search_dirs.append(os.path.join(base_dir, app_settings.CUSTOM_SPRITES_SUB_DIRECTORY))
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            print(f"🔍 Searching in: {search_dir}")
            for root, dirs, files in os.walk(search_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                if "AnimData.xml" in files:
                    xml_path = os.path.join(root, "AnimData.xml")
                    
                    if filter_list:
                        folder_name = os.path.basename(root)
                        
                        should_include = False
                        for filter_item in filter_list:
                            if "pokemon" in search_dir and folder_name.isdigit():
                                if filter_item.isdigit() and folder_name == filter_item.zfill(4):
                                    should_include = True
                                    break
                            elif folder_name.lower() == filter_item.lower():
                                should_include = True
                                break
                        
                        if not should_include:
                            continue
                    
                    anim_files.append(xml_path)
                    print(f"✅ Found AnimData.xml: {xml_path}")
    
    print(f"📁 Total AnimData.xml files found: {len(anim_files)}")
    return anim_files

def parse_animdata_xml(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    animations = []

    base_animations = {}
    for anim_elem in root.findall(".//Anim"):
        name = anim_elem.findtext("Name")
        if not name:
            continue
            
        if anim_elem.findtext("CopyOf"):
            continue
            
        frame_w = int(anim_elem.findtext("FrameWidth", default="0"))
        frame_h = int(anim_elem.findtext("FrameHeight", default="0"))
        
        durations = []
        durations_elem = anim_elem.find("Durations")
        if durations_elem is not None:
            for d in durations_elem.findall("Duration"):
                val = int(d.text)
                durations.append(round((1.0 / 60.0) * val * 1000.0, 0))
        
        total_frames = len(durations) if durations else 1
        
        anim_path = f"{name}-Anim.png"
        offsets_path = f"{name}-Offsets.png"
        shadow_path = f"{name}-Shadow.png"
        anim_data = AnimationData(name, anim_path, offsets_path, shadow_path, 
                                 frame_w, frame_h, durations, total_frames)
        animations.append(anim_data)
        base_animations[name] = anim_data
    
    for anim_elem in root.findall(".//Anim"):
        name = anim_elem.findtext("Name")
        copy_of = anim_elem.findtext("CopyOf")
        
        if copy_of and name:
            source_anim = base_animations.get(copy_of)
            if source_anim:
                copied_anim = AnimationData(
                    name=name,
                    anim_path=f"{copy_of}-Anim.png",
                    offsets_path=f"{copy_of}-Offsets.png",
                    shadow_path=f"{copy_of}-Shadow.png",
                    frame_width=source_anim.frame_width,
                    frame_height=source_anim.frame_height,
                    durations=source_anim.durations.copy(),
                    total_frames=source_anim.total_frames
                )
                animations.append(copied_anim)
                print(f"✅ Copied animation: {name} → {copy_of} (uses {copy_of}-Anim.png)")
            else:
                print(f"⚠️ Could not copy {name} from {copy_of}: source not found")
    
    return animations

def determine_pokemon_info_from_path(xml_path: str, pokemon_map):
    normalized_path = os.path.normpath(xml_path)
    parts = normalized_path.split(os.sep)
    
    is_custom = "custom" in parts
    
    if is_custom:
        try:
            custom_index = parts.index("custom")
            if custom_index + 1 < len(parts):
                folder_name = parts[custom_index + 1]
                print(f"🎨 Custom Pokémon detected: {folder_name}")
                return "-1", folder_name, "Custom", True
            else:
                print(f"⚠️ Could not determine custom Pokémon name from path: {xml_path}")
                return None, None, None, False
        except ValueError:
            print(f"⚠️ Could not find custom in path: {xml_path}")
            return None, None, None, False
    else:
        try:
            pokemon_index = parts.index("pokemon")
            if pokemon_index + 1 < len(parts):
                folder_name = parts[pokemon_index + 1]
                if folder_name.isdigit():
                    pokemon_id = folder_name
                    pokemon_info = pokemon_map.get(pokemon_id.zfill(4), {"name": "Unknown", "generation": "Unknown"})
                    print(f"🔢 Regular Pokémon detected: {pokemon_id} - {pokemon_info['name']}")
                    return pokemon_id, pokemon_info["name"], pokemon_info["generation"], False
                else:
                    print(f"⚠️ Skipping {xml_path}: invalid Pokémon folder name '{folder_name}'")
                    return None, None, None, False
            else:
                print(f"⚠️ Could not determine Pokémon folder from path: {xml_path}")
                return None, None, None, False
        except ValueError:
            print(f"⚠️ Could not find pokemon in path: {xml_path}")
            return None, None, None, False