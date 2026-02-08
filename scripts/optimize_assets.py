import os
import shutil
import glob
from PIL import Image

# Configuration
ASSETS_DIR = "assets"
ARCHIVE_DIR = os.path.join(ASSETS_DIR, "_archive")
CATEGORIES = ["units", "spells", "titans", "spellcasters", "consumables"]

def optimize_assets():
    print("Starting Asset Optimization...")
    converted_count = 0
    
    for category in CATEGORIES:
        src_dir = os.path.join(ASSETS_DIR, category)
        archive_category_dir = os.path.join(ARCHIVE_DIR, category)
        
        if not os.path.exists(src_dir):
            continue
            
        # Ensure archive dir exists
        if not os.path.exists(archive_category_dir):
            os.makedirs(archive_category_dir)

        # Find all PNGs in the main folder (newly added ones)
        png_files = glob.glob(os.path.join(src_dir, "*.png"))
        
        for png_path in png_files:
            filename = os.path.basename(png_path)
            basename = os.path.splitext(filename)[0]
            webp_path = os.path.join(src_dir, f"{basename}.webp")
            archive_path = os.path.join(archive_category_dir, filename)
            
            print(f"Processing {filename}...")
            
            try:
                # 1. Convert to WebP if missing
                if not os.path.exists(webp_path):
                    with Image.open(png_path) as img:
                        img.save(webp_path, "WEBP", quality=90)
                    print(f"  [+] Created {basename}.webp")
                else:
                    print(f"  [.] {basename}.webp already exists")

                # 2. Archive the PNG
                if os.path.exists(archive_path):
                    # versioning collision? - overwrite for now as per "update" logic
                    os.remove(archive_path)
                
                shutil.move(png_path, archive_path)
                print(f"  [>] Archived to {archive_path}")
                converted_count += 1
                
            except Exception as e:
                print(f"  [!] Failed to process {filename}: {e}")

    print(f"\nOptimization Complete. Processed {converted_count} files.")

if __name__ == "__main__":
    optimize_assets()
