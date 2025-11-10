# Author: HeartoLazor
# Description: Bounding box optimization for spritesheets

import os
import json
from typing import Dict, Tuple
from PIL import Image

# The left and right sides calculation of the offsets is not correct for certain pokemons in the body.json after applying this optimization
# So while this bug is not fixed, skip affected pokemons
optimization_skip_hack_list = [
    "0001", #Bulbasaur
    "0004", #Charmander
    "0005", #Charmeleon
    "0019", #Rattata
    "0023", #Ekans
    "0027", #Sandshrew
    "0038", #Ninetales
    "0040", #Wigglytuff
    "0043", #Oddish
    "0044", #Gloom
    "0045", #Vileplume
    "0048", #Venonat
    "0050", #Digglet
    "0051", #Dugtrio
    "0056", #Mankey
    "0067", #Machoke
    "0068", #Machamp
    "0069", #Bellsprout
    "0071", #Victreebel
    "0072", #Tentacool
    "0077", #Ponyta
    "0081", #Magnemite
    "0085", #Dodrio
    "0090", #Shellder
    "0094", #Gengar
    "0096", #Drowzee
    "0097", #Hypno
    "0098", #Krabby
    "0099", #Kingler
    "0103", #Exeggutor
    "0104", #Cubone
    "0105", #Marowak
    "0106", #Hitmonlee
    "0107", #Hitmonchan
    "0108", #Lickytung
    "0110", #Weezing
    "0114", #Tangela
    "0116", #Horsea
    "0117", #Seadra
    "0122", #Mr. Mime
    "0124", #Jinx
    "0127", #Pinsir
    "0134", #Vaporeon
    "0135", #Jolteon
    "0142", #Aerodactil
    "0144", #Articuno
    "0145", #Zapdos
    "0152", #Chikorita
    "0159", #Croconaw
    "0161", #Sentret
    "0162", #Furret
    "0170", #Chinchou
    "0187", #Hoppip
    "0192", #Sunflora
    "0195", #Quagsire
    "0196", #Espeon
    "0204", #Pineco
    "0209", #Snubull
    "0210", #Granbull
    "0214", #Heracross
    "0218", #Slugma
    "0223", #Remoraid
    "0232", #Dophan
    "0235", #Smeargle
    "0243", #Raikou
    "0244", #Entei
    "0245", #Suicune
    "0251", #Celebi
    "0252", #Treecko
    "0253", #Grovyle
    "0254", #Sceptile
    "0259", #Marshtomp
    "0260", #Swamper
    "0261", #Poochyena
    "0262", #Mightyena
    "0271", #Lombre
    "0274", #Nuzleaf
    "0280", #Ralts
    "0286", #Breloom
    "0298", #Azurill
    "0299", #Nosepass
    "0302", #Sableye
    "0303", #Mawile
    "0304", #Aron
    "0307", #Meditite
    "0309", #Electrike
    "0311", #Plusle
    "0312", #Minum
    "0313", #Volbeat
    "0315", #Roselia
    "0322", #Numel
    "0323", #Camerupt
    "0324", #Torkoal
    "0325", #Spoink
    "0328", #Trapinch
    "0329", #Vibrava
    "0335", #Zangosee
    "0337", #Lunatone
    "0342", #Crawdaunt
    "0343", #Baltoy
    "0345", #Lileep
    "0346", #Cradily
    "0352", #Kecleon
    "0354", #Banette
    "0357", #Tropius
    "0359", #Absol
    "0372", #Shelgon
    "0377", #Regirock
    "0378", #Regice
    "0379", #Registeel
    "0383", #Groudon
    "0385", #Jirachi
    "0386", #Deoxis
    "0387", #Turtwig
    "0388", #Grotle
    "0391", #Monferno
    "0398", #Staraptor
    "0400", #Birabel
    "0403", #Shinx
    "0404", #Luxio
    "0405", #Luxray
    "0407", #Roserade
    "0417", #Pachirisu
    "0422", #Gastrodon
    "0425", #Drifloon
    "0427", #Buneary
    "0433", #Chingling
    "0434", #Stunky
    "0435", #Skuntank
    "0442", #Spiritomb
    "0445", #Garchomp
    "0446", #Munchlax
    "0448", #Lucario
    "0452", #Magnezone
    "0473", #Mamoswine
    "0474", #Porygon-Z
    "0475", #Gallade
    "0479", #Rotom
    "0492", #Shaymin
    "0495", #Snivy
    "0496", #Servine
    "0503", #Samurott
    "0508", #Stoutland
    "0517", #Munna
    "0518", #Musharna
    "0520", #Unfezant
    "0521", #Roggenrola
    "0522", #Boldore
    "0531", #Audino
    "0532", #Timburr
    "0533", #Gurdurr
    "0540", #Sewaddle
    "0543", #Venipede
    "0544", #Whirlipede
    "0545", #Scolipede
    "0549", #Lilligant
    "0550", #Basculin
    "0551", #Sandile
    "0552", #Krokorok
    "0555", #Darmanitan
    "0556", #Maractus
    "0559", #Scraggy
    "0560", #Scrafty
    "0561", #Sigilyph
    "0567", #Archeops
    "0568", #Trubbish
    "0571", #Zoroark
    "0576", #Gothitelle
    "0578", #Duosion
    "0584", #Vanilluxe
    "0585", #Deerling
    "0587", #Emolga
    "0590", #Foongus
    "0602", #Tynamo
    "0607", #Litwick
    "0602", #Fraxure
    "0602", #Cubchoo
    "0622", #Golett
    "0625", #Bisharp
    "0628", #Braviary
    "0629", #Vullaby
    "0631", #Heatmor
    "0632", #Durant
    "0640", #Virizion
    "0643", #Reshiram
    "0644", #Zekrom
    "0645", #Landorus
    "0646", #Kyurem
    "0647", #Keldeo
    "0651", #Quilladin
    "0655", #Delphox
    "0657", #Frogadier
    "0664", #Scatterbug
    "0667", #Litleo
    "0671", #Florges
    "0672", #Skiddo
    "0676", #Furfrou
    "0678", #Meowstic
    "0686", #Inkay
    "0688", #Binacle
    "0689", #Barbaracle
    "0691", #Dragalge
    "0698", #Amaura
    "0699", #Aurorus
    "0700", #Sylveon
    "0701", #Hawlucha
    "0702", #Dedenne
    "0704", #Goomy
    "0705", #Slygoo
    "0706", #Goodra
    "0709", #Trevenant
    "0712", #Bergmite
    "0713", #Noibat
    "0714", #Noiverm
    "0717", #Yvetal
    "0724", #Decidueye
    "0727", #Incineroar
    "0728", #Popplio
    "0729", #Brionne
    "0733", #Toucannon
    "0737", #Charjabug
    "0739", #Crabrawler
    "0744", #Rockruff
    "0747", #Mareanie
    "0748", #Mudbray
    "0766", #Passimian
    "0768", #Golisopod
    "0769", #Sandygast
    "0778", #Mimikyu
    "0780", #Drampa
    "0783", #Hakamo o
    "0784", #Kommo o
    "0785", #Tapu koko
    "0791", #Solgaleo
    "0794", #Buzzwole
    "0795", #Pheromosa
    "0796", #Xurkitree
    "0799", #Guzzlord
    "0801", #Magearna
    "0806", #Blacephalon
    "0807", #Zeraora
    "0811", #Thwackey
    "0812", #Rillaboom
    "0813", #Scorbunny
    "0816", #Sobble
    "0828", #Thievul
    "0830", #Eldegoss
    "0833", #Chewtle
    "0834", #Drednaw
    "0841", #Flapple
    "0843", #Silicobra
    "0844", #Sandaconda
    "0851", #Centiskorch
    "0852", #Clobbopus
    "0858", #Hatterene
    "0861", #Grimmsnarl
    "0862", #Obstagoon
    "0863", #Cursola
    "0869", #Alcremie
    "0875", #Escue
    "0876", #Indeedee
    "0877", #Morpeko
    "0879", #Copperajah
    "0880", #Dracozolt
    "0882", #Dracovish
    "0883", #Arctovish
    "0884", #Duraludon
    "0887", #Dragapult
    "0888", #Zacian
    "0894", #Regieleki
    "0901", #Ursaluna
    "0911", #Skeledirge
    "0919", #Nymble
    "0920", #Lokix
    "0921", #Pawmi
    "0922", #Pawmot
    "0939", #Bellibolt
    "0957", #Tinkatink
    "0959", #Tinkaton
    "0960", #Wiglett
    "0961", #Wugtrio
    "0963", #Finizen
    "0964", #Palafin
    "0968", #Orthworm
    "0971", #Greavard
    "0972", #Houndstone
    "0974", #Cetoddle
    "0975", #Cetitan
    "0980", #Clodsire
    "0981", #Farigiraf
    "0982", #Dudunsparse
    "0983", #Kingambit
    "0985", #Scream Tail
    "0989", #Sandy Shocks
    "0991", #Iron Bundle
    "0998", #Ting Lu
    "1004", #Chi Yu
    "1008", #Miraidon
    "1009", #Walking Wake
    "1011", #Dipplin
    "1015", #Munkidori
    "1016", #Fezandipiti
    "1020", #Gougin Fire
    "1024", #Terapagos
]

def calculate_global_bounding_box(spritesheet_path: str, frame_width: int, frame_height: int, total_frames: int, frames_per_row: int) -> Tuple[int, int, int, int]:
    """Calculate the minimum bounding box that contains all non-transparent pixels from all frames"""
    print(f"📐 Calculating global bounding box for {spritesheet_path}...")
    
    with Image.open(spritesheet_path) as spritesheet:
        spritesheet = spritesheet.convert('RGBA')
        
        min_x = frame_width
        min_y = frame_height
        max_x = 0
        max_y = 0
        
        for frame_index in range(total_frames):
            row = frame_index // frames_per_row
            col = frame_index % frames_per_row
            
            x_start = col * frame_width
            y_start = row * frame_height
            x_end = x_start + frame_width
            y_end = y_start + frame_height
            
            frame = spritesheet.crop((x_start, y_start, x_end, y_end))
            
            # Get bounding box of non-transparent pixels
            bbox = frame.getbbox()
            if bbox:
                frame_min_x, frame_min_y, frame_max_x, frame_max_y = bbox
                
                min_x = min(min_x, frame_min_x)
                min_y = min(min_y, frame_min_y)
                max_x = max(max_x, frame_max_x)
                max_y = max(max_y, frame_max_y)
        
        print(f"✅ Bounding box: ({min_x}, {min_y}) to ({max_x}, {max_y})")
        print(f"📏 Original size: {frame_width}x{frame_height}, Optimized size: {max_x-min_x}x{max_y-min_y}")
        
        return min_x, min_y, max_x, max_y

def optimize_spritesheet(spritesheet_path: str, output_path: str, frame_width: int, frame_height: int, 
                        total_frames: int, frames_per_row: int) -> Tuple[int, int, int, int]:
    """Optimize spritesheet by cropping to minimum bounding box"""
    min_x, min_y, max_x, max_y = calculate_global_bounding_box(
        spritesheet_path, frame_width, frame_height, total_frames, frames_per_row
    )
    
    optimized_width = max_x - min_x
    optimized_height = max_y - min_y
    
    print(f"✂️ Cropping spritesheet to {optimized_width}x{optimized_height}...")
    
    with Image.open(spritesheet_path) as spritesheet:
        spritesheet = spritesheet.convert('RGBA')
        
        rows_needed = (total_frames + frames_per_row - 1) // frames_per_row
        new_width = optimized_width * frames_per_row
        new_height = optimized_height * rows_needed
        
        optimized_sheet = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        
        for frame_index in range(total_frames):
            row = frame_index // frames_per_row
            col = frame_index % frames_per_row
            
            # Original frame position
            orig_x_start = col * frame_width
            orig_y_start = row * frame_height
            
            # Cropped region from original
            crop_box = (orig_x_start + min_x, orig_y_start + min_y, 
                       orig_x_start + max_x, orig_y_start + max_y)
            cropped_frame = spritesheet.crop(crop_box)
            
            # Position in optimized spritesheet
            new_x = col * optimized_width
            new_y = row * optimized_height
            
            optimized_sheet.paste(cropped_frame, (new_x, new_y))
        
        optimized_sheet.save(output_path, 'PNG')
        print(f"✅ Optimized spritesheet saved: {output_path}")
        
        return optimized_width, optimized_height, min_x, min_y

def update_json_offsets(body_json_path: str, crop_offset_x: int, crop_offset_y: int, 
                       new_width: int, new_height: int, original_width: int, original_height: int):
    """Update offsets in body.json after optimization"""
    print(f"📝 Updating JSON offsets: {body_json_path}...")
    
    with open(body_json_path, 'r', encoding='utf-8') as f:
        body_data = json.load(f)
    
    # Update body dimensions
    if 'FrontBody' in body_data:
        body_data['FrontBody']['BodySize'] = {"Width": new_width, "Length": new_height}
        body_data['FrontBody']['Portrait']['SourceRectangle'] = {'X':0, 'Y':0, "Width": new_width, "Height": new_height}
        portrait_offset_x = body_data['FrontBody']['Portrait']['Offset']['X']
        portrait_offset_y = body_data['FrontBody']['Portrait']['Offset']['Y']
        body_data['FrontBody']['Portrait']['Offset'] = {'X': portrait_offset_x + crop_offset_x, 'Y': portrait_offset_y + crop_offset_y}
    if 'RightBody' in body_data:
        body_data['RightBody']['BodySize'] = {"Width": new_width, "Length": new_height}
    if 'BackBody' in body_data:
        body_data['BackBody']['BodySize'] = {"Width": new_width, "Length": new_height}
    if 'LeftBody' in body_data:
        body_data['LeftBody']['BodySize'] = {"Width": new_width, "Length": new_height}
    
    # Update frame offsets in all animations
    def update_frame_offsets(animations):
        frames_updated = 0
        for anim in animations:
            if 'Offset' in anim:
                anim['Offset']['X'] = anim['Offset']['X'] - crop_offset_x
                anim['Offset']['Y'] = anim['Offset']['Y'] - crop_offset_y
                frames_updated += 1
        return frames_updated
    
    total_frames_updated = 0
    
    for body_type in ['FrontBody', 'RightBody', 'BackBody', 'LeftBody']:
        if body_type in body_data:
            # Update IdleAnimation
            if 'IdleAnimation' in body_data[body_type]:
                frames_updated = update_frame_offsets(body_data[body_type]['IdleAnimation'])
                total_frames_updated += frames_updated
                print(f"  📋 Updated {frames_updated} frames in {body_type}.IdleAnimation")
            
            # Update MovementAnimations
            if 'MovementAnimation' in body_data[body_type]:
                frames_updated = update_frame_offsets(body_data[body_type]['MovementAnimation'])
                total_frames_updated += frames_updated
                print(f"  📋 Updated {frames_updated} frames in {body_type}.MovementAnimation")
    
    # Save updated JSON
    with open(body_json_path, 'w', encoding='utf-8') as f:
        json.dump(body_data, f, indent=2)
    
    print(f"✅ Updated JSON: {total_frames_updated} frame offsets, body dimensions, and portrait")

def optimize_sprite_output(output_dir: str, original_width: int, original_height: int, 
                          total_frames: int, frames_per_row: int = 32):
    """Main optimization function for a sprite output directory"""
    print(f"🎯 Optimizing sprite output: {output_dir}")
    
    spritesheet_path = os.path.join(output_dir, "body.png")
    body_json_path = os.path.join(output_dir, "body.json")
    
    if not os.path.exists(spritesheet_path) or not os.path.exists(body_json_path):
        print(f"⚠️ Skipping optimization: required files not found in {output_dir}")
        return
        
    # Optimize spritesheet
    temp_spritesheet = os.path.join(output_dir, "body_optimized.png")
    new_width, new_height, crop_x, crop_y = optimize_spritesheet(
        spritesheet_path, temp_spritesheet, original_width, original_height, 
        total_frames, frames_per_row
    )
    
    # Replace original with optimized
    os.replace(temp_spritesheet, spritesheet_path)
    
    # Update JSON
    update_json_offsets(body_json_path, crop_x, crop_y, new_width, new_height, original_width, original_height)
    
    print(f"🎉 Optimization complete for {output_dir}")
    print(f"📊 Size reduction: {original_width}x{original_height} → {new_width}x{new_height}")
    print(f"📊 Area reduction: {original_width * original_height} → {new_width * new_height} pixels ({((1 - (new_width * new_height) / (original_width * original_height)) * 100):.1f}% smaller)")

    return new_width, new_height

def batch_optimize_all_outputs(base_output_dir: str, spritesheet_mapping: Dict) -> Dict:
    """Optimize all generated spritesheets in batch and return updated mapping"""
    print(f"🚀 Starting batch optimization for {len(spritesheet_mapping)} spritesheets...")
    
    updated_mapping = spritesheet_mapping.copy()
    
    for variant_name, sprite_data in spritesheet_mapping.items():
        pokemon_id: str = sprite_data['pokemon_id']
        if(pokemon_id not in optimization_skip_hack_list):
            output_dir = sprite_data['directory']
            original_width = sprite_data['max_width']
            original_height = sprite_data['max_height']
            total_frames = sprite_data['total_frames']
            frames_per_row = sprite_data.get('frames_per_row', 32)
            
            print(f"\n--- Optimizing {variant_name} ---")
            try:
                new_width, new_height = optimize_sprite_output(output_dir, original_width, original_height, total_frames, frames_per_row)
                
                if new_width and new_height:
                    updated_mapping[variant_name]['max_width'] = new_width
                    updated_mapping[variant_name]['max_height'] = new_height
                    print(f"📐 Updated dimensions: {original_width}x{original_height} → {new_width}x{new_height}")
                    
            except Exception as e:
                print(f"❌ Failed to optimize {variant_name}: {e}")
        else:
            print(f"⚠️ Skipping optimization: Optimization disabled for {variant_name} while the left and right sides calculation of the offsets is not correct in the body.json for certain pokemons after applying this optimization")
    
    print(f"\n🎊 Batch optimization completed!")
    return updated_mapping