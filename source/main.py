# Author: HeartoLazor
# Description: Main CLI and processing pipeline

import os
import argparse
import time
from collections import defaultdict
from typing import Tuple
from data_models.enums import VariantProcessingMode
from data_models.animation_models import AnimationSet
from file_handlers.xml_parser import find_animdata_files, parse_animdata_xml, determine_pokemon_info_from_path, get_variant_path_from_xml
from utils.path_utils import load_pokemon_names, get_variation_type, is_variant_in_csv, get_variant_index_from_path
from image_processing.sprite_processor import generate_spritesheets, add_debug_numbers_to_spritesheet
from config.settings import AppSettings, app_settings

class ProcessingMetrics:
    """Simple metrics tracking for processing"""
    def __init__(self):
        self.files_processed = 0
        self.total_frames_generated = 0
        self.processing_time = 0.0
        self.errors_count = 0
        self.warnings_count = 0
        self.files_by_type = {}
    
    def record_processing(self, frames_count: int, processing_time: float, file_type: str = "unknown"):
        self.files_processed += 1
        self.total_frames_generated += frames_count
        self.processing_time += processing_time
        self.files_by_type[file_type] = self.files_by_type.get(file_type, 0) + 1
    
    def record_error(self):
        self.errors_count += 1
    
    def record_warning(self):
        self.warnings_count += 1
    
    def print_summary(self):
        print(f"\n📊 Processing Summary:")
        print(f"   Files processed: {self.files_processed}")
        print(f"   Total frames: {self.total_frames_generated}")
        print(f"   Total time: {self.processing_time:.2f}s")
        
        if self.files_processed > 0:
            avg_time = self.processing_time / self.files_processed
            print(f"   Average time per file: {avg_time:.2f}s")
        else:
            print(f"   Average time per file: 0.00s")
            
        print(f"   Errors: {self.errors_count}")
        print(f"   Warnings: {self.warnings_count}")
        
        if self.files_by_type:
            print(f"   Files by type: {self.files_by_type}")

def time_execution(description: str = ""):
    """Decorator para medir tiempo de ejecución"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            time_taken = end_time - start_time
            desc = description or func.__name__
            print(f"⏱️ {desc} executed in {time_taken:.2f} seconds")
            return result
        return wrapper
    return decorator

def process_single_animation_file(xml_path: str, pokemon_map: dict, settings: AppSettings, pokemon_variant_counter: defaultdict, variant_mode: VariantProcessingMode = VariantProcessingMode.ALL_VARIANTS, log_file: str = "stardew_missing.log"):
    """Process a single animation file with timing and metrics"""
    start_time = time.time()
    
    try:
        print(f"📄 Processing: {xml_path}")
        
        pokemon_id, pokemon_name, generation, is_custom = determine_pokemon_info_from_path(xml_path, pokemon_map)
        
        if pokemon_id is None:
            print(f"⏭️ Skipping {xml_path}: could not determine Pokémon info")
            return None, "unknown", time.time() - start_time, None

        # Get pokemon csv data
        pokemon_data = pokemon_map.get(pokemon_id, {})
        
        # Determine variant path and index
        variant_path = get_variant_path_from_xml(xml_path, os.path.dirname(xml_path))
        variant_index = get_variant_index_from_path(pokemon_data, variant_path)
        
        # If variant not found in CSV and we're in minimal mode, skip it
        if variant_mode == VariantProcessingMode.MINIMAL_VARIANTS and variant_index == -1:
            print(f"⏭️ Skipping {variant_path}: not in variations_paths")
            return None, "skipped", time.time() - start_time, None
        
        # If variant index not found, use counter-based approach
        if variant_index == -1:
            variant_index = pokemon_variant_counter[pokemon_id] + 1
            pokemon_variant_counter[pokemon_id] += 1
        else:
            # Update counter to the maximum of current and found index
            pokemon_variant_counter[pokemon_id] = max(pokemon_variant_counter[pokemon_id], variant_index)

        # Determine if should process in this mode
        should_process, skip_reason = should_process_variant(
            variant_index, variant_mode, pokemon_data, variant_path
        )

        if not should_process:
            print(f"⏭️ Skipping variant {variant_index} for {pokemon_id} ({skip_reason})")
            return None, "skipped", time.time() - start_time, None

        # Get variation type
        variation_type = get_variation_type(pokemon_data, variant_index)
        
        # Create variant suffix
        if variation_type:
            variant_suffix = f"{app_settings.NAME_SEPARATOR}{variation_type}"
            print(f"🎯 Using named variation: {variation_type}")
        else:
            if variant_index == 1:
                variant_suffix = ""
                print(f"🏠 Base variant - no suffix")
            else:
                variant_suffix = f"{app_settings.NAME_SEPARATOR}{variant_index - 1}"
                print(f"🔢 Using numeric variation: {variant_index - 1}")

        # Create variant name
        if is_custom:
            variant_name = pokemon_name + variant_suffix
        else:
            variant_name = f"{pokemon_id}{app_settings.NAME_SEPARATOR}{pokemon_name}{variant_suffix}"

        print(f"🎯 Creating AnimationSet: {variant_name} (index: {variant_index}, mode: {variant_mode})")
        if variation_type:
            print(f"   Variation type: {variation_type}")

        # Parse animations
        animations = parse_animdata_xml(xml_path)
        print(f"📊 Found {len(animations)} animations in {xml_path}")
        
        # Create AnimationSet
        anim_set = AnimationSet(
            pokemon_id=pokemon_id,
            pokemon_name=pokemon_name,
            variant_name=variant_name,
            generation=generation,
            directory=os.path.dirname(xml_path),
            max_width=0,
            max_height=0,
            animations=animations,
        )

        # Filter animations for Stardew
        from config.stardew_config import load_stardew_mapping_config
        global_offsets = anim_set.filter_animations_for_stardew(anim_set.pokemon_id, log_file)
        anim_set.global_offsets = global_offsets

        # Compute max width/height based on mapped Stardew animations
        relevant_anims = [
            next((a for a in anim_set.animations if a.name == st_map.pokemon_anim_name), None)
            for st_map in anim_set.stardew_animations
        ]
        relevant_anims = [a for a in relevant_anims if a is not None]

        if relevant_anims:
            anim_set.max_width = max(a.frame_width for a in relevant_anims)
            anim_set.max_height = max(a.frame_height for a in relevant_anims)

        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Determine file type
        file_type = "custom" if is_custom else "pokemon"
        
        print(f"✅ Successfully processed {variant_name} in {processing_time:.2f}s")
        return anim_set, file_type, processing_time, variation_type
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Failed to parse {xml_path} in {processing_time:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return None, "unknown", processing_time, None

def should_process_variant(current_variant_count: int, variant_mode: VariantProcessingMode, pokemon_data: dict, variant_path: str) -> Tuple[bool, str]:
    """Determine if a variant should be processed based on the processing mode and CSV data."""
    
    if variant_mode == VariantProcessingMode.ALL_VARIANTS:
        return True, ""
    
    elif variant_mode == VariantProcessingMode.MINIMAL_VARIANTS:
        # Get variant index from path
        variant_index = get_variant_index_from_path(pokemon_data, variant_path)
        
        if variant_index == -1:
            # Variant not found in CSV, skip it
            return False, "not in variations_paths"
        
        # Check if this variant is enabled in minimal_variants
        if (variant_index - 1) < len(pokemon_data.get("minimal_variants", [])):
            is_enabled = pokemon_data["minimal_variants"][variant_index - 1] == 1
            if is_enabled:
                return True, "enabled in minimal_variants"
            else:
                return False, "disabled in minimal_variants"
        else:
            # No minimal_variants data, use default behavior
            if is_variant_in_csv(pokemon_data, variant_path):
                return True, "in variations_paths (no minimal_variants data)"
            else:
                return False, "not in variations_paths"
    
    elif variant_mode == VariantProcessingMode.SKIP_VARIANTS:
        # Only process the first variant (base)
        if current_variant_count == 1:
            return True, "base variant"
        else:
            return False, "skip-variants mode"
    
    return True, ""

def process_animations_parallel(anim_files: list, pokemon_map: dict, settings: AppSettings, variant_mode: VariantProcessingMode = VariantProcessingMode.ALL_VARIANTS, metrics: ProcessingMetrics = None):
    """Process multiple animation files"""
    all_sets = []
    variation_types_used = {}
    sets_with_variation_data = []
    
    pokemon_variant_counter = defaultdict(int)
    
    print(f"🔧 Processing {len(anim_files)} files...")
    print(f"🎛️  Variant mode: {variant_mode.value}")
    
    for i, xml_path in enumerate(anim_files, 1):
        print(f"\n--- Processing file {i}/{len(anim_files)} ---")
        
        result = process_single_animation_file(xml_path, pokemon_map, settings, pokemon_variant_counter, variant_mode)
        
        if result and result[0]:  # result[0] is the AnimationSet
            anim_set, file_type, processing_time, variation_type = result
            
            sets_with_variation_data.append({
                'anim_set': anim_set,
                'variation_type': variation_type,
                'file_type': file_type,
                'processing_time': processing_time
            })
            
            all_sets.append(anim_set)
            
            # Track variation types for summary
            if variation_type:
                pokemon_id = anim_set.pokemon_id
                if pokemon_id not in variation_types_used:
                    variation_types_used[pokemon_id] = []
                variation_types_used[pokemon_id].append(variation_type)
            
            # Update metrics if provided
            if metrics:
                # Calculate total frames for this animation set
                frames_count = 0
                for stardew_anim in anim_set.stardew_animations:
                    frames_count += (len(stardew_anim.pokemon_frames_index_front) +
                                   len(stardew_anim.pokemon_frames_index_right) +
                                   len(stardew_anim.pokemon_frames_index_back) +
                                   len(stardew_anim.pokemon_frames_index_left))
                
                metrics.record_processing(frames_count, processing_time, file_type)
        else:
            if metrics and result and result[1] != "skipped":
                metrics.record_error()
    
    print(f"\n📊 Variant processing summary ({variant_mode.value}):")
    processed_count = 0
    skipped_count = 0
    
    for pokemon_id, total_count in pokemon_variant_counter.items():
        if total_count > 0:
            processed = sum(1 for data in sets_with_variation_data if data['anim_set'].pokemon_id == pokemon_id)
            skipped = total_count - processed
            
            processed_count += processed
            skipped_count += skipped
            
            variation_info = ""
            if pokemon_id in variation_types_used:
                variation_info = f" [types: {', '.join(variation_types_used[pokemon_id])}]"
            
            if skipped > 0:
                print(f"   {pokemon_id}: {processed} processed, {skipped} skipped{variation_info}")
            else:
                print(f"   {pokemon_id}: {processed} processed{variation_info}")
    
    if skipped_count > 0:
        print(f"   Total: {processed_count} processed, {skipped_count} skipped")
    
    return sets_with_variation_data

def validate_inputs(args, settings: AppSettings):
    """Validate all input parameters using settings"""
    # Validate base directory
    if not os.path.isdir(args.base_dir):
        print(f"❌ Base directory '{args.base_dir}' is not a valid directory.")
        return False
    
    # Validate CSV file
    if not os.path.isfile(args.csv_path):
        print(f"❌ CSV file '{args.csv_path}' is not a valid file.")
        return False
    
    # Validate output directory using settings
    output_dir = settings.OUTPUT_DIR
    try:
        os.makedirs(output_dir, exist_ok=True)
        # Test writing a file
        test_file = os.path.join(output_dir, ".write_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except (PermissionError, OSError) as e:
        print(f"❌ Cannot write to output directory {output_dir}: {e}")
        return False
    
    # Validate required directories exist
    required_dirs = [
        settings.TEMPLATES_DIR,
        settings.CONFIG_DIR,
        settings.IMAGES_DIR
    ]
    
    for req_dir in required_dirs:
        if not req_dir.exists():
            print(f"⚠️ Warning: Required directory {req_dir} does not exist")
            # Try to create it
            try:
                req_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {req_dir}")
            except Exception as e:
                print(f"❌ Could not create directory {req_dir}: {e}")
    
    print(f"✅ All inputs validated successfully")
    print(f"   Base directory: {args.base_dir}")
    print(f"   Output directory: {output_dir}")
    print(f"   Workers: {settings.MAX_WORKERS}")
    print(f"   Frames per row: {settings.FRAMES_PER_ROW}")
    print(f"   Debug mode: {settings.ENABLE_DEBUG_FRAMES}")
    
    return True

@time_execution("Total processing")
def main():
    parser = argparse.ArgumentParser(
        description="Parse Pokémon AnimData.xml files and filter for Stardew animations."
    )
    parser.add_argument("base_dir", help="Base directory containing Pokémon folders.")
    parser.add_argument("csv_path", help="CSV file with Pokémon number, name, and generation mapping.")
    parser.add_argument("--output", "-o", default="generated", help="Output directory for generated spritesheets")
    parser.add_argument("--frames-per-row", "-f", type=int, default=32, help="Frames per row in output spritesheet")
    parser.add_argument("--debug-frames", "-d", action="store_true", help="Add frame numbers for debugging")
    parser.add_argument("--no-variations-as-subfolders", action="store_true", help="Store variants in root folder instead of subfolders")
    parser.add_argument("--filter", nargs="+", help="Filter Pokémon by ID or custom name (e.g., 0120 CoolPokesonaName 0230)")
    parser.add_argument("--custom-only", action="store_true", help="Only process custom sprites, ignoring the pokemon folder")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of worker threads for parallel processing")
    
    parser.add_argument(
        "--variant-mode", 
        type=VariantProcessingMode, 
        choices=list(VariantProcessingMode),
        default=VariantProcessingMode.ALL_VARIANTS,
        help="Variant processing mode: all-variants (default), minimal-variants, or skip-variants"
    )

    parser.add_argument(
        "--optimize", 
        action="store_true", 
        help="Optimize spritesheets by cropping transparent areas (reduces file size)"
    )

    parser.add_argument(
        "--deduplicate", 
        action="store_true", 
        help="Remove duplicate frames from spritesheets (reduces file size)"
    )
 
    parser.add_argument(
        "--pot-optimize", 
        action="store_true", 
        help="Optimize spritesheets to power-of-two dimensions (better GPU performance)"
    )

    parser.add_argument(
        "--max-texture-size",
        type=int,
        default=4096,
        help="Maximum texture size for POT optimization (default: 4096)"
    )
    args = parser.parse_args()

    # Create settings from arguments
    settings = AppSettings.from_args(args)
    
    base_dir = args.base_dir
    if not os.path.isdir(base_dir):
        parser.error(f"'{base_dir}' is not a valid directory.")
    if not os.path.isfile(args.csv_path):
        parser.error(f"'{args.csv_path}' is not a valid CSV file.")

    # Check directory structure using settings
    pokemon_dir = os.path.join(base_dir, settings.POKEMON_SPRITES_SUB_DIRECTORY)
    custom_dir = os.path.join(base_dir, settings.CUSTOM_SPRITES_SUB_DIRECTORY)
    
    print(f"📁 Base directory: {base_dir}")
    print(f"📂 Pokemon directory exists: {os.path.exists(pokemon_dir)}")
    print(f"📂 Custom directory exists: {os.path.exists(custom_dir)}")
    
    # Parse filter list
    filter_list = args.filter if args.filter else None
    custom_only = args.custom_only
    
    if filter_list:
        print(f"🔍 Filtering for: {filter_list}")
    if custom_only:
        print(f"🎨 Processing custom sprites only")
    
    if os.path.exists(pokemon_dir) and not custom_only:
        pokemon_contents = os.listdir(pokemon_dir)
        print(f"📋 Pokemon directory contents: {len(pokemon_contents)} folders")
    
    if os.path.exists(custom_dir):
        custom_contents = os.listdir(custom_dir)
        print(f"📋 Custom directory contents: {len(custom_contents)} folders")

    # Validate inputs using settings
    if not validate_inputs(args, settings):
        return [], {}

    # Load Pokémon mapping
    pokemon_map = load_pokemon_names(args.csv_path)
    
    # Find animation files using settings
    anim_files = find_animdata_files(base_dir, filter_list, custom_only)
    if not anim_files:
        print("❌ No animation files found!")
        return [], {}
    
    print(f"📁 Found {len(anim_files)} animation files")
    
    # Initialize metrics
    metrics = ProcessingMetrics()
    
    # Process animations using settings
    print("🔄 Starting animation processing...")
    sets_with_variation_data = process_animations_parallel(anim_files, pokemon_map, settings, args.variant_mode, metrics)

    if not sets_with_variation_data:
        print("❌ No valid animation sets processed!")
        return [], {}
    
    all_sets = [data['anim_set'] for data in sets_with_variation_data]
    
    # Print processing summary so far
    print("\n📈 Animation Processing Complete:")
    metrics.print_summary()
    
    # Generate spritesheets using settings
    print("\n🎨 Generating spritesheets...")
    spritesheet_start = time.time()
    
    variations_as_subfolders = not args.no_variations_as_subfolders
    spritesheet_mapping = generate_spritesheets(
        sets_with_variation_data, 
        str(settings.OUTPUT_DIR), 
        settings.FRAMES_PER_ROW, 
        settings.ENABLE_DEBUG_FRAMES,
        variations_as_subfolders
    )
    
    spritesheet_time = time.time() - spritesheet_start
    print(f"⏱️ Spritesheet generation took: {spritesheet_time:.2f}s")
    
    # Update total processing time
    metrics.processing_time += spritesheet_time
    
    # Calculate total frames from spritesheet mapping
    total_frames_from_spritesheets = sum(data['total_frames'] for data in spritesheet_mapping.values())
    metrics.total_frames_generated = total_frames_from_spritesheets
    
    # Final summary
    print(f"\n🎉 Final Results:")
    metrics.print_summary()
    
    print(f"✅ Successfully generated {len(spritesheet_mapping)} spritesheets")
    print(f"📁 Output directory: {settings.OUTPUT_DIR}")
    
    # === OPTIMIZE WHITE SPACE STEP ===
    if args.optimize:
        print("\n🔄 Starting spritesheet optimization...")
        from utils.bbox_optimizer import batch_optimize_all_outputs
        spritesheet_mapping = batch_optimize_all_outputs(str(settings.OUTPUT_DIR), spritesheet_mapping)
    else:
        print("\nℹ️  Optimization skipped (use --optimize to enable)")
    
    # === DEDUPLICATION STEP ===
    if args.deduplicate:
        print("\n🔄 Starting frame deduplication...")
        from utils.frame_deduplicator import batch_deduplicate_frames
        spritesheet_mapping = batch_deduplicate_frames(str(settings.OUTPUT_DIR), spritesheet_mapping)
    else:
        print("\nℹ️  Frame deduplication skipped (use --deduplicate to enable)")

    # === POWER OF TWO STEP ===
    if args.pot_optimize:
        print("\n🔄 Starting power-of-two optimization...")
        from utils.pot_optimizer import batch_pot_optimization
        spritesheet_mapping = batch_pot_optimization(
            str(settings.OUTPUT_DIR), 
            spritesheet_mapping, 
            args.max_texture_size
        )
    else:
        print("\nℹ️  Power-of-two optimization skipped (use --pot-optimize to enable)")

    # === DEBUG STEP ===
    if args.debug_frames:
        print("\n🔢 Adding debug numbers to spritesheets...")
        for variant_name, sprite_data in spritesheet_mapping.items():
            try:
                output_dir = sprite_data['directory']
                spritesheet_path = os.path.join(output_dir, "body.png")
                frame_width = sprite_data['max_width']
                frame_height = sprite_data['max_height']
                total_frames = sprite_data['total_frames']
                frames_per_row = sprite_data.get('frames_per_row', 32)
                
                add_debug_numbers_to_spritesheet(
                    spritesheet_path, frame_width, frame_height, 
                    total_frames, frames_per_row, sprite_data.get('frame_mapping', {})
                )
            except Exception as e:
                print(f"⚠️ Failed to add debug to {variant_name}: {e}")
    else:
        print("\nℹ️ Debug numbers skipped (use --debug-frames to enable)")
    return all_sets, spritesheet_mapping

if __name__ == "__main__":
    all_sets, spritesheet_mapping = main()