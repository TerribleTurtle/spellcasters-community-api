import glob
import json
import os


def remove_hero_speed():
    heroes_dir = os.path.join(os.path.dirname(__file__), "../../data/heroes")
    files = glob.glob(os.path.join(heroes_dir, "*.json"))

    print(f"Found {len(files)} hero files.")

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        if "movement_speed" in data:
            print(f"Removing movement_speed from {os.path.basename(filepath)}")
            del data["movement_speed"]

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")  # Add trailing newline
        else:
            print(f"Skipping {os.path.basename(filepath)} (no movement_speed)")


if __name__ == "__main__":
    remove_hero_speed()
