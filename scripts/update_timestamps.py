import json
import sys
import os
from datetime import datetime

def update_timestamp(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Current UTC time in ISO format
        current_time = datetime.utcnow().isoformat() + "Z"
        
        # Update or add the last_modified field
        data['last_modified'] = current_time
        
        # Remove date_modified if it exists (legacy cleanup)
        if 'date_modified' in data:
            del data['date_modified']

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n') # Ensure trailing newline
            
        print(f"Updated: {file_path}")
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_timestamps.py <file1> <file2> ...")
        sys.exit(1)

    files = sys.argv[1:]
    updated_count = 0

    for file_path in files:
        if not file_path.endswith('.json'):
            continue
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        if update_timestamp(file_path):
            updated_count += 1

    print(f"Total files updated: {updated_count}")

if __name__ == "__main__":
    main()
