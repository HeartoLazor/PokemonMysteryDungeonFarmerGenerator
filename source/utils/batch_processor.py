# Author: HeartoLazor
# Description: Batch animation processing utilities

import os
import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_models.animation_models import AnimationSet
from file_handlers.xml_parser import parse_animdata_xml, determine_pokemon_info_from_path
from utils.metrics import ProcessingMetrics
from utils.validators import validate_animation_set

class AnimationSetBuilder:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self._animation_set = None
        self._pokemon_map = None
    
    def set_pokemon_map(self, pokemon_map: dict):
        self._pokemon_map = pokemon_map
        return self
    
    def from_xml_path(self, xml_path: str) -> 'AnimationSetBuilder':
        """Build AnimationSet from XML file path"""
        if not self._pokemon_map:
            raise ValueError("Pokemon map must be set before calling from_xml_path")
        
        pokemon_id, pokemon_name, generation, is_custom = determine_pokemon_info_from_path(xml_path, self._pokemon_map)
        
        if not pokemon_id:
            return self
            
        animations = parse_animdata_xml(xml_path)
        
        variant_name = self._generate_variant_name(pokemon_id, pokemon_name, is_custom)
        
        self._animation_set = AnimationSet(
            pokemon_id=pokemon_id,
            pokemon_name=pokemon_name,
            variant_name=variant_name,
            generation=generation,
            directory=os.path.dirname(xml_path),
            max_width=0,
            max_height=0,
            animations=animations,
        )
        return self
    
    def with_stardew_mapping(self, log_file: str = "stardew_missing.log") -> 'AnimationSetBuilder':
        """Apply Stardew mapping"""
        if self._animation_set:
            from config.stardew_config import load_stardew_mapping_config
            global_offsets = self._animation_set.filter_animations_for_stardew(
                self._animation_set.pokemon_id, log_file
            )
            self._animation_set.global_offsets = global_offsets
        return self
    
    def calculate_dimensions(self) -> 'AnimationSetBuilder':
        """Calculate maximum dimensions"""
        if self._animation_set and self._animation_set.stardew_animations:
            relevant_anims = [
                next((a for a in self._animation_set.animations 
                      if a.name == st_map.pokemon_anim_name), None)
                for st_map in self._animation_set.stardew_animations
            ]
            relevant_anims = [a for a in relevant_anims if a is not None]
            
            if relevant_anims:
                self._animation_set.max_width = max(a.frame_width for a in relevant_anims)
                self._animation_set.max_height = max(a.frame_height for a in relevant_anims)
        return self
    
    def build(self) -> Optional[AnimationSet]:
        """Return the built AnimationSet"""
        result = self._animation_set
        self.reset()
        return result
    
    def _generate_variant_name(self, pokemon_id: str, pokemon_name: str, is_custom: bool) -> str:
        """Generate variant name based on Pokémon type"""
        if is_custom:
            return pokemon_name
        else:
            return f"{pokemon_id} - {pokemon_name}"

def process_single_animation_file(xml_path: str, pokemon_map: dict, log_file: str = "stardew_missing.log") -> Optional[AnimationSet]:
    """Process a single animation file with error handling"""
    start_time = time.time()
    try:
        builder = AnimationSetBuilder()
        anim_set = (builder
                   .set_pokemon_map(pokemon_map)
                   .from_xml_path(xml_path)
                   .with_stardew_mapping(log_file)
                   .calculate_dimensions()
                   .build())
        
        if anim_set:
            # Validate the result
            is_valid, errors = validate_animation_set(anim_set)
            if not is_valid:
                print(f"⚠️ Validation warnings for {anim_set.variant_name}:")
                for error in errors:
                    print(f"   - {error}")
        is_custom = "custom" in xml_path.lower()
        file_type = "custom" if is_custom else "pokemon"
        
        processing_time = time.time() - start_time
        print(f"✅ Processed {file_type}: {anim_set.variant_name if anim_set else 'Unknown'} in {processing_time:.2f}s")
        
        return anim_set, file_type, processing_time
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Failed to process {xml_path} in {processing_time:.2f}s: {e}")
        return None, "unknown", processing_time

def process_animations_parallel(anim_files: List[str], pokemon_map: dict, max_workers: int = 4, metrics: ProcessingMetrics = None) -> List[AnimationSet]:
    """Process multiple animation files in parallel con métricas"""
    all_sets = []
    
    print(f"🔧 Processing {len(anim_files)} files with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_single_animation_file, xml_path, pokemon_map): xml_path 
            for xml_path in anim_files
        }
        
        completed = 0
        total = len(anim_files)
        
        for future in as_completed(future_to_file):
            xml_path = future_to_file[future]
            completed += 1
            
            try:
                result = future.result()
                if result and result[0]:
                    anim_set, file_type, processing_time = result
                    all_sets.append(anim_set)
                    
                    if metrics:
                        frames_count = sum(len(st_map.pokemon_frames_index_front) + 
                                         len(st_map.pokemon_frames_index_right) +
                                         len(st_map.pokemon_frames_index_back) +
                                         len(st_map.pokemon_frames_index_left)
                                         for st_map in anim_set.stardew_animations)
                        metrics.record_processing(frames_count, processing_time, file_type)
                    
                    print(f"✅ [{completed}/{total}] {file_type}: {anim_set.variant_name} ({processing_time:.2f}s)")
                else:
                    if metrics:
                        metrics.record_error()
                    print(f"❌ [{completed}/{total}] Failed: {xml_path}")
                    
            except Exception as e:
                if metrics:
                    metrics.record_error()
                print(f"❌ [{completed}/{total}] Unexpected error: {e}")
    
    return all_sets