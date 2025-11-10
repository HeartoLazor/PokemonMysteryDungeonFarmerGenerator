# Author: HeartoLazor
# Description: Path and file name utilities

import csv
import sys
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from config.settings import app_settings
except ImportError:
    print("⚠️ Could not import from config, using default settings")

VARIATIONS_SEPARATOR_STRING = ";"

def load_pokemon_names(csv_path: str):
    """Load Pokémon number-to-name and generation mapping from CSV with variant data."""
    mapping = {}
    try:
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                num = row["number"].zfill(4)
                
                pokemon_data = {
                    "name": row["name"],
                    "generation": row["generation"],
                    "variations_paths": [],
                    "variation_types": [],
                    "minimal_variants": [] 
                }
                
                # Process variations_paths if exists
                if "variations_paths" in row and row["variations_paths"]:
                    paths = row["variations_paths"].split(VARIATIONS_SEPARATOR_STRING)
                    # Clean and normalize paths - remove trailing slashes for matching
                    pokemon_data["variations_paths"] = [
                        p.strip().rstrip('/').replace('\\', '/')
                        for p in paths if p.strip()
                    ]
                    
                # Process variation_types if exists
                if "variation_types" in row and row["variation_types"]:
                    types = row["variation_types"].split(VARIATIONS_SEPARATOR_STRING)
                    pokemon_data["variation_types"] = [t.strip() for t in types if t.strip()]
                
                # Process minimal_variants if exists
                if "minimal_variants" in row and row["minimal_variants"]:
                    minimal_flags = row["minimal_variants"].split(VARIATIONS_SEPARATOR_STRING)
                    pokemon_data["minimal_variants"] = [
                        int(flag.strip()) if flag.strip().isdigit() else 1
                        for flag in minimal_flags if flag.strip()
                    ]
                else:
                    # Default to all enabled if column doesn't exist
                    pokemon_data["minimal_variants"] = [1] * len(pokemon_data["variations_paths"])
                
                # Ensure all arrays have the same length
                expected_length = len(pokemon_data["variations_paths"])
                if len(pokemon_data["variation_types"]) < expected_length:
                    pokemon_data["variation_types"].extend([''] * (expected_length - len(pokemon_data["variation_types"])))
                if len(pokemon_data["minimal_variants"]) < expected_length:
                    pokemon_data["minimal_variants"].extend([1] * (expected_length - len(pokemon_data["minimal_variants"])))

                mapping[num] = pokemon_data
                print(f"✅ Loaded {num}: {pokemon_data['name']} - Minimal variants: {pokemon_data['minimal_variants']}")
                
        return mapping
    except Exception as e:
        print(f"❌ Error loading Pokémon names from {csv_path}: {e}")
        return {}

def determine_variant_name_counter(pokemon_id: str, counter_map: dict, pokemon_data: dict) -> str:
    """Determine variant suffix considering named variations from CSV."""
    current_count = counter_map[pokemon_id] + 1
    
    # Check if this variant has a named variation
    variation_type = get_variation_type(pokemon_data, current_count)
    
    if variation_type:
        # Named variation (e.g., "shiny")
        return f"{app_settings.NAME_SEPARATOR}{variation_type}"
    else:
        # Numeric variation
        if current_count == 1:
            return ""  # Base variant without number
        else:
            return f"{app_settings.NAME_SEPARATOR}{current_count - 1}"

def generate_variant_name(pokemon_id: str, pokemon_name: str, is_custom: bool, variant_suffix: str = "") -> str:
    """Generate variant name using NAME_SEPARATOR from settings."""
    base_name = f"{pokemon_id}{app_settings.NAME_SEPARATOR}{pokemon_name}" if not is_custom else pokemon_name
    
    return f"{base_name}{variant_suffix}"

def get_variation_type(pokemon_data: dict, variant_index: int) -> str:
    """Get the variation type for a specific variant index."""
    if "variation_types" in pokemon_data and variant_index - 1 < len(pokemon_data["variation_types"]):
        return pokemon_data["variation_types"][variant_index - 1]
    return None

def get_variation_path(pokemon_data: dict, variant_index: int) -> str:
    """Get the variation path for a specific variant index."""
    if "variations_paths" in pokemon_data and variant_index - 1 < len(pokemon_data["variations_paths"]):
        return pokemon_data["variations_paths"][variant_index - 1]
    return None

def is_variant_in_csv(pokemon_data: dict, variant_path: str) -> bool:
    """Check if a variant path is in the variations_paths list."""
    if "variations_paths" not in pokemon_data:
        return True  # If not available, process all
    
    # Normalize paths for comparison
    normalized_input = variant_path.replace('\\', '/').strip().rstrip('/')
    csv_paths = [p.replace('\\', '/').strip().rstrip('/') for p in pokemon_data["variations_paths"]]
    
    return normalized_input in csv_paths

def extract_base_variant_name(variant_name: str, variation_type: str = None) -> str:
    """Extract the base variant name without variation suffixes."""
    if not variation_type:
        return variant_name
    
    base_parts = variant_name.split(app_settings.NAME_SEPARATOR)
    if len(base_parts) > 1:
        return app_settings.NAME_SEPARATOR.join(base_parts[:-1])
    
    return variant_name

def get_variant_index_from_path(pokemon_data: dict, variant_path: str) -> int:
    """Get the variant index from the path by matching with variations_paths."""
    if "variations_paths" not in pokemon_data:
        return 1  # Default to base variant if no data
    
    # Normalize both paths to use forward slashes and remove trailing slashes
    normalized_input = variant_path.replace('\\', '/').strip().rstrip('/')
    csv_paths = [p.replace('\\', '/').strip().rstrip('/') for p in pokemon_data["variations_paths"]]
    
    print(f"🔍 DEBUG Path Matching:")
    print(f"   Input: '{normalized_input}'")
    print(f"   CSV Paths: {csv_paths}")
    
    try:
        index = csv_paths.index(normalized_input) + 1
        print(f"   Match found at index: {index}")
        return index
    except ValueError:
        print(f"   No match found")
        return -1  # Not found

def is_variant_enabled_in_minimal(pokemon_data: dict, variant_index: int) -> bool:
    """Check if a variant is enabled in minimal_variants mode."""
    if "minimal_variants" not in pokemon_data:
        return True  # Default to enabled if no data
    
    if variant_index - 1 < len(pokemon_data["minimal_variants"]):
        return pokemon_data["minimal_variants"][variant_index - 1] == 1
    
    return True  # Default to enabled if index out of range