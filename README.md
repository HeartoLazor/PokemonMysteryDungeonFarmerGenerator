# Pokemon Mystery Dungeon Farmer Generator
A tool that converts Pokémon Mystery Dungeon sprites from https://sprites.pmdcollab.org/ into Fashion Sense compatible body animations for Stardew Valley. This generator processes Pokemon Mystery Dungeon AnimData.xml files and creates optimized Fashion Sense body spritesheets with proper JSON configuration.

This is the source code of the mod available at: https://www.nexusmods.com/stardewvalley/mods/39038

If you want to just be a pokemon, use the Nexus ready to play version. If you want to export your custom pmd sprite, follow this Readme.

# Features
**Automated Conversion:** Converts PMD sprites to Fashion Sense format

**Multiple Variant Support:** Handles different Pokémon forms and variations

**Optimization Support:** Supports Bounding box optimization, Cleanup of frame duplicates and Power-of-two texture optimization.

**Debug Tools:** Support for frame debug generation and helpers to create customized sprites. 

**Custom Sprite Support**: Support for custom Pokémon Mystery Dungeon sprites.

# Prerequisites
Python 3.8+

Pillow (PIL) library

CSV with information about each pokemon (optional, included in the repository), this can be generated using the script available at this repository: https://github.com/HeartoLazor/pmdsprite_scrapper

# Installation
Clone this repository

Install required dependencies:

    pip install pillow

# How to use

Run without any parameters:

    python main.py /path/to/pmd/sprites /path/to/pokemon.csv

Full parameter list:

    python main.py /path/to/pmd/sprites /path/to/pokemon.csv  --output generated --frames-per-row 32 --debug-frames --optimize --deduplicate --pot-optimize --variant-mode all-variants

# Project Structure

    PokemonMysteryDungeonFarmerGenerator/
    ├── config/                 # Internal pythonconfiguration files
    ├── data_models/            # Data models and enums
    ├── file_handlers/          # File processing utilities
    ├── image_processing/       # Sprite processing logic
    ├── templates/              # JSON templates for Fashion Sense body.json
    ├── utils/                  # Utility functions
    ├── generator_configs/      # Default configuration and Pokémon-specific configuration overrides
    ├── sprites/                # Sprite directories (ignored in git and can be changed in parameters)
    │   ├── pokemon/            # Pokémon sprites (expected to be inside the sprites folder, here we put the pokemons available inside the sprite folder from https://github.com/PMDCollab/SpriteCollab/ )
    │   └── custom/             # Custom sprites (expected to be inside the sprites folder, here we put custom edits, supports any non numbered folder name to avoid pokemon numbering folder clashes)
    ├── main.py                 # Main entry point
    └── README.md               # This file

# Command Line Options

**Required Arguments**
base_dir: Base directory containing Pokémon folders

csv_path: CSV file with Pokémon number, name, and generation mapping

**Optional Arguments:**
--output, -o: Output directory (default: "generated")

--frames-per-row, -f: Frames per row in spritesheet (default: 32), --pot-optimize ignores this option, as it reorganizes the spritesheet to ensure pot size.

--debug-frames, -d: Add frame numbers for debugging

--workers, -w: Number of worker threads (default: 4)

--optimize: Optimize spritesheets by cropping transparent areas

--deduplicate: Remove duplicate frames. Warning: this step is very slow.

--pot-optimize: Optimize to power-of-two dimensions

--variant-mode: Variant processing mode (all-variants, minimal-variants, skip-variants):

All variants: all pokemon sprites and variations are available, including shinnies, galar, etc.

Minimal variants: hand picked variants, uses the pokemon_data.csv minimal_variants column data.

Skip variants: Only the base pokemon is available.

# Create Custom Sprites:
Using the --debug-frames command argument, the system will output source frames with the used frames transparent background color changed to a solid color. you can use that for a guide of which frames you need to edit in the original sprite to create your Custom OC, when you have all the frames edited you can change the folder name (example: AwesomePokemonOC) and copy it to sprite/custom/ folder. Remember to update the Shadow.png and Offsets.png if you change where the legs are placed in the original sprite, more information about this topic here: https://wiki.pmdo.pmdcollab.org/Tutorial:PMD_Sprite_Format

# Fashion Sense Integration
**Generated Files**
For each Pokémon variant, the generator creates:

**body.png:** The Fashion Sense body spritesheet.

**body.json:** Fashion Sense body configuration file.

**eyes.png:** Eye dummy invisible sprite. It's the same for every generated Pókemon.

**credits.txt:** Attribution file (if source provided)

# Stardew Valley recommended Installation
1. Download the mod available at Nexus: https://www.nexusmods.com/stardewvalley/mods/39038

Alt: copy the folder inside Mods of this repository, this folder has the same files available at the Mod at nexus, including the Invisible sprites, don't forget to update the manifest. Ideally follow this path for exporting your Custom OCS and Pokesona PMD sprites copying the source sprites to sprites/custom/ before generation.

2. Copy the variation type generated folder to your Stardew Valley mods directory:

For example if you used skip_variations, inside ./generated/ will generate a folder with a similar name, so in this example, copy the contents inside ./generated/skip-variations/ to the Bodies inside the Fashion Sense Mod folder.
 
3. Copy the variation type generated folder to your Stardew Valley mods directory:

Stardew Valley/Mods/PMD Sprites Mod Name/Bodies/your generated files

Ensure Fashion Sense mod (https://www.nexusmods.com/stardewvalley/mods/9969) and Bobbing Disabler mod (https://www.nexusmods.com/stardewvalley/mods/39035) is installed and enabled.

Launch Stardew Valley and select the Pokémon body using the Fashion Sense's Hand mirror, don't forget to use invisible sprites and change modulation. Here is a video that show how to configure the Body inside Stardew Valley: https://www.youtube.com/watch?v=-UZJP_m8uUA

# Generator configuration files
There are multiple files that helps to configure the output of the generator:

**templates:** Those are files that defines how the body.json will be created and the fields that will be edited, those have keywords that the script will replace. Those can be edited to make future proof against changes in Fashion Sense body.json. 

**pokemon_data.csv:** This is like a "database" with all of the pokemons number, names, type and filters, generated from https://sprites.pmdcollab.org/ using this scrapper: https://github.com/HeartoLazor/pmdsprite_scrapper

The CSV should contain this columns in the same order (using Pikachu as example):

number: Pokémon number (example: 0025)

name: Pokémon name (example: Pikachu)

generation: Generation number (example: 1)

variations_paths: Semicolon-separated variant paths, those follows the same relative paths inside the sprites/pokemon/ folder, so for pikachu it's /sprites/pokemon/0025/ (example: 0025/;0025/0006/;0025/0007/;0025/0000/0001/;0025/0006/0001/;0025/0007/0001/;0025/0000/0000/0002/;0025/0000/0001/0002/)

variation_types: Semicolon-separated variant names with the same element number as the variations_paths, (example: Normal;Libre;Cosplay;Shiny;Libre Shiny;Cosplay Shiny;Female;Shiny Female). Each entry is the name of one of the variations available in the path, for example: 0025/ is Normal, 0025/0006/ is Libre, 0025/0007/ it's Cosplay and so on.

minimal_variants: Semicolon-separated flags for minimal variants, this is only used when the minimal-variants flag is used, this uses a manual filter to enable (1) or disable (0) each variant. Should be the same quantity of entries as variations_paths (example: 1;1;0;1;1;1;1;1  In this example the Pikachu Cosplay is disabled)

**generator_configs:** 
Create JSON files in generator_configs/ for Pokémon-specific settings: Files that defines how to map the sprites into the Stardew Valley spritesheet and other json data. There is a default file (default_config.json) and can be overriden for each pokemon or sprite creating another json file with the same Name, for example if you have a folder with the name 0025 in sprites/pokemon/ you can create 0025.json to override specific settings, same with the sprites/custom/ where if you have a folder with the name AwesomePokemonOC you can create AwesomePokemonOC.json to override settings. The most common settings to override are head_offset and portrait offset to make it match inside the game, because those properties are very hard to auto guess from the sprite information. Also with this you can override animations for actions inside stardew valley. _Remember that all players should have the same generated file to view the same animations in multiplayer._

**Here is a description of all the attributes:**

global_offsets: offsets applied to all rendered sprites in different areas. You can modify each section in this areas without copy all of the properties in the override, if a property is missing it uses the default value available at the default_config.json.
    
    "pokemon_sprite_offset_x": 0, "pokemon_sprite_offset_y": 0: the offset of the sprite rendered inside of stardew valley in each axis. 
    
    "pokemon_portrait_offset_x": 0, "pokemon_portrait_offset_y": 0: the offset of the sprite rendered in the pause menu and in the map screen.
    
    "accessory_offset": 0, "head_offset": -4, "leg_offset": 0, "shoe_offset": 0, "body_offset": 0, "arms_offset": 0: offset of each part available inside of stardew valley, for example if you want to match the Stardew Valley's hats with the sprite in a better way, you need to edit the head_offset value.

animations: this whole section defines how the sprites will be mapped into stardew valley, need to override all the section for changing any spritesheet mapping, so the best is to just copy the whole animation section from the default_config.json into the override json and edit it.

There are many animation types, they have common properties as:

    "type": "portrait": The animation type, can have five values: default, force_frame, range_start_end, range_start_negative_end, portrait, repeat_frame_count.
    
    "name": "harvest": Which animation will represent into Stadew Valley, unique value used for clarity and organization.
    
    "fallback_names": ["Hop", "Idle"]: Each animation available for PMDSprites, follow this format Name-Anim.png and other files that follows the same pattern, for example Hop-Anim.png, Hop-Offsets.png and Hop-Shadow.png, here we map the fallback for those animation, in the example we will use Hop if we find it, if not found we will use Idle and so on.

    "body_type": "idle_animation": Animation section where the animation will be placed in the Fashion Sense's body.json, with two possible values: idle_animation, movement_animation. See Fashion Sense wiki for more information.
    
    "use_front_only": true: When this flag is enabled, the system will use the first row of sprites from the PMDsprite source. This is useful for some Stardew Animation that are only player with the player facing the front, as the eating animation for example.
    
    "discard_distance": 12: If the system detects that a frame had moved the feet far away from another animation, the animation is discarded. This is to avoid certain animation that looks bad when ported to stardew valley because of the character moving far away from the horizontal center.
    
    "conditions_names": ["IsHarvesting"]: Array with conditions that will use to play the animation, most of the time you will just use the same condition. Prefer to use one condition for each animation mapping, because the system doesn't handle well multiple conditions per animation. The system internally optimizes the generated spritesheet to avoid repeating sprites.
    
    "conditions_group_names" : ["IsIdle"]: conditions group names available at your conditions.json in the Mods/[FS] PokemonMysteryDungeonFarmer/
    
    "duration_mult": 1.0: How much the animation will be scaled up or down, for example in default animations Walk is shared by run and walk stardew animation, with the difference that run is 25% faster (0.75)
    
    "debug_font_color": [0, 0, 255, 192]: Only used when the debug-frames flag is enabled, represent the color used for each debugged frame of the animation.

    "sprite_offset_x": 0, "sprite_offset_y": 0: the animation offset of the sprite rendered inside of stardew valley in each axis. This is applied on top of the global offset.

Animations properties per animation type:

    "portrait": is the frame that will be used in the map and pause menu inside Stardew Valley. The system picks the frame number defined in the field "frame", for example: "frame": 0 will use the first frame. There is only one portrait entry per Pokemon.

    "default": will pick all the frames in order without special properties.

    "force_frame": will pick a forced frame defined in the "frame" field, for example: "frame": 0 will use the first frame.

    "range_start_end": will pick a range of frames for the animation, with two properties: frame_start which defines the frame where the animation will start and frame_end which defines where the frame will end.

    "range_start_negative_end": will pick a range of frames  based in an array for start and end, with two properties: frame_range_start an array which defines the frames that will be picked at start and frame_range_end which defines which frames will be picked from the end (in negative values). For example "frame_range_start": [2, 3] and  "frame_range_end": [-2, -1] with an animation with 10 frames from 0 index, will end in the frames [2, 3, 8, 9].

    "repeat_frame_count": will repeat a set of frames a number of times defined by the frame_quantity field. For example. "frame_quantity": 10 with an animation with only three frames, will result in this loop: [0, 1, 2, 0, 1, 2, 0, 1, 2, 0] 

# Common Issues
Missing Animations: Check stardew_missing.log for unmapped animations.

Pokemon folders ending with a number instead of a Name, example: "Pikachu - 4" instead of "Pikachu - Shiny", this means the value for the variants was not found at the pokemon_data.csv, check the variant paths to see if it match, chance is that the data of the sprites downloaded from the pmd sprite github doesn't match with the one scrapped from the webpage and it requires to be updated, this most of the time can be done manually, but if there there is many of the sprites missmatching, it's better to just to add the missing pokemon and use the scrapper

# Credits
Mod Author: [HeartoLazor](https://linktr.ee/HeartoLazor)

Fashion Sense Mod: by [Floogen](https://github.com/Floogen/)

All of the awesome people that ripped PMD sprites available at https://sprites.pmdcollab.org/#/?creditsMode=true

# Special Notes:

This repository doesn't include any Pokemon Sprites, It's only a tool to generate Stardew Valley Fashion Sense sprites from the Pokemon Mystery Dungeon animation format.
