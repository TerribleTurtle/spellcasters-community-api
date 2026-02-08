import os
import shutil
import glob

ARCHIVE_DIR = "assets/_archive"
ASSETS_DIR = "assets"

CATEGORIES = ["units", "spells", "titans", "spellcasters", "consumables"]

def restore_assets():
    print("Restoring assets from archive for re-processing...")
    restored_count = 0
    
    for category in CATEGORIES:
        src_dir = os.path.join(ARCHIVE_DIR, category)
        
        if not os.path.exists(src_dir):
            continue
            
        # Get all PNGs in archive
        png_files = glob.glob(os.path.join(src_dir, "*.png"))
        
        for png_path in png_files:
            filename = os.path.basename(png_path)
            # Move back to ASSETS root for sorting script to pick up
            dest_path = os.path.join(ASSETS_DIR, filename)
            
            try:
                shutil.move(png_path, dest_path)
                print(f"Restored {filename} -> {ASSETS_DIR}/")
                restored_count += 1
            except Exception as e:
                print(f"Error restoring {filename}: {e}")

    print(f"\nRestoration Complete. Restored {restored_count} files.")

if __name__ == "__main__":
    restore_assets()
