import pytest
import os
import sys

# Ensure scripts module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import config

def test_spawner_referential_integrity(data_loader):
    """
    Ensures that any mechanic that reference a 'unit_id' (e.g. Spawners)
    points to a valid Unit that exists in data/units/.
    """
    errors = []
    
    # 1. Collect all valid Unit IDs
    valid_unit_ids = set()
    for unit in data_loader.get("units", []):
        if "entity_id" in unit:
            valid_unit_ids.add(unit["entity_id"])
            
    # 2. Check Spells and Units for Spawner mechanics
    # Spawners can be in 'units', 'spells', or 'spellcasters' (abilities)
    
    # Check Units & Spells
    for folder in ["units", "spells"]:
        for item in data_loader.get(folder, []):
            filename = item.get("_filename", "unknown")
            mechanics = item.get("mechanics", {})
            spawners = mechanics.get("spawner", [])
            
            for spawner in spawners:
                unit_id = spawner.get("unit_id")
                if unit_id and unit_id not in valid_unit_ids:
                    errors.append(f"[{folder}/{filename}] Spawner references unknown unit_id: '{unit_id}'")

    assert len(errors) == 0, "\n".join(errors)

def test_upgrade_target_tags(data_loader):
    """
    Ensures that Upgrades target tags that actually exist on at least one Unit.
    """
    errors = []
    
    # 1. Collect all existing Tags from Units
    all_unit_tags = set()
    for unit in data_loader.get("units", []):
        for tag in unit.get("tags", []):
            all_unit_tags.add(tag)
            
    # 2. Check Upgrades
    for upgrade in data_loader.get("upgrades", []):
        filename = upgrade.get("_filename", "unknown")
        target_tags = upgrade.get("target_tags", [])
        
        for tag in target_tags:
            if tag not in all_unit_tags:
                errors.append(f"[{filename}] Upgrade targets tag '{tag}' which no unit seems to have.")
                
    assert len(errors) == 0, "\n".join(errors)

def test_entity_id_matches_filename(data_loader):
    """
    Ensures that the 'entity_id' matches the filename (without extension).
    """
    errors = []
    
    for caster in data_loader.get("heroes", []):
        filename = caster.get("_filename", "")
        # Remove extension
        basename = os.path.splitext(filename)[0]
        
        ent_id = caster.get("entity_id")
        
        if ent_id != basename:
            errors.append(f"[{filename}] entity_id '{ent_id}' does not match filename '{basename}'")
            
    assert len(errors) == 0, "\n".join(errors)
