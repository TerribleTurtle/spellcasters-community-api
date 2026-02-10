import os
import shutil
import glob
from PIL import Image

import config

# Configuration
ASSETS_DIR = config.ASSETS_DIR
SOURCE_DIR_NAME = "source"
CATEGORIES = ["units", "spells", "titans", "spellcasters", "consumables"]

def optimize_assets():
    print("Starting Asset Optimization...")
    converted_count = 0
    
    for category in CATEGORIES:
        src_dir = os.path.join(ASSETS_DIR, category)
        source_category_dir = os.path.join(src_dir, SOURCE_DIR_NAME)
        
        if not os.path.exists(src_dir):
            continue
            
        # Ensure source dir exists
        if not os.path.exists(source_category_dir):
            os.makedirs(source_category_dir)

        # Find all PNGs in the main folder (newly added ones)
        png_files = glob.glob(os.path.join(src_dir, "*.png"))
        
        for png_path in png_files:
            filename = os.path.basename(png_path)
            basename = os.path.splitext(filename)[0]
            webp_path = os.path.join(src_dir, f"{basename}.webp")
            source_path = os.path.join(source_category_dir, filename)
            
            print(f"Processing {filename}...")
            
            try:
                # 1. Convert to WebP (Always overwrite if PNG is new)
                with Image.open(png_path) as img:
                    img.save(webp_path, "WEBP", quality=90)
                print(f"  [+] Updated {basename}.webp")

                # 2. Move original to source folder
                if os.path.exists(source_path):
                    # overwritten if exists
                    os.remove(source_path)
                
                shutil.move(png_path, source_path)
                print(f"  [>] Moved source to {source_path}")
                converted_count += 1
                
            except Exception as e:
                print(f"  [!] Failed to process {filename}: {e}")

    print(f"\nOptimization Complete. Processed {converted_count} files.")

if __name__ == "__main__":
    optimize_assets()
