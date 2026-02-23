"""
Data Audit Script (V2)

Performs deep analytical audits of the JSON data layer. Validates balances,
checks constraint logic, and calculates aggregate statistics on entities.
Usually run before major releases.
"""

import json
import os
import statistics
from collections import defaultdict
from pathlib import Path

try:
    from jsonschema import ValidationError, validators
    from referencing import Registry, Resource
except ImportError:
    print("CRITICAL: 'referencing' library or 'jsonschema' >= 4.18 not found. Cannot proceed.")
    exit(1)

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SCHEMAS_DIR = os.path.join(PROJECT_ROOT, "schemas", "v2")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "audit_report_v2.md")

HEURISTIC_MAP = {
    "magic_school": "spells.schema.json",
    "health": "units.schema.json",
    "attack_damage": "units.schema.json",
    "effect_type": "consumables.schema.json",
    "hero_class": "heroes.schema.json",
    "starting_mana": "heroes.schema.json",
    "element": "titans.schema.json",
    "upgrade_type": "upgrades.schema.json",
}


def load_json(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    print("Starting Strict Validation Protocol (V2 - referencing)...")

    # 1. Load Schemas into Registry
    registry = Registry()
    schemas_by_name = {}  # Map 'spells.schema.json' -> schema content

    print("Loading schemas...")
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        for file in files:
            if not file.endswith(".schema.json"):
                continue
            filepath = os.path.join(root, file)
            schema = load_json(filepath)
            if not schema:
                continue

            # Create Resource
            # We use absolute file URI as the ID
            abs_uri = Path(filepath).as_uri()
            resource = Resource.from_contents(schema)
            registry = registry.with_resource(abs_uri, resource)

            # Map relative name for inference
            rel_path = os.path.relpath(filepath, SCHEMAS_DIR).replace(os.sep, "/")
            schemas_by_name[rel_path] = schema

            # Also register under relative name? referencing is strict about URIs.
            # But we can assume the $ids in files might be missing, so we rely on URIs.

    validation_failures = []
    orphaned_files = []
    mapping_matrix = []
    data_registry = []

    print(f"Registry loaded with {len(schemas_by_name)} schemas.")

    # 2. Walk Data
    for root, _dirs, files in os.walk(DATA_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, DATA_DIR)
            folder_name = os.path.dirname(rel_path)

            data = load_json(filepath)
            if data is None:
                validation_failures.append(f"File `{rel_path}`: Invalid JSON syntax.")
                continue

            # Infer Schema
            schema_name = None
            confidence = "None"

            # Explicit $schema
            if "$schema" in data:
                ref = data["$schema"]
                # Normalize typical relative path "../../schemas/v2/foo.json"
                if "schemas/v2/" in ref.replace("\\", "/"):
                    fname = ref.replace("\\", "/").split("schemas/v2/")[-1]
                    if fname in schemas_by_name:
                        schema_name = fname
                        confidence = "High (Explicit)"
                elif os.path.basename(ref) in schemas_by_name:
                    schema_name = os.path.basename(ref)
                    confidence = "High (Explicit - Basename)"

            # Heuristic
            if not schema_name:
                for k, v in HEURISTIC_MAP.items():
                    if k in data and v in schemas_by_name:
                        schema_name = v
                        confidence = "Medium (Heuristic)"
                        break

            # Directory Fallback
            if not schema_name:
                if f"{folder_name}.schema.json" in schemas_by_name:
                    schema_name = f"{folder_name}.schema.json"
                    confidence = "Low (Directory)"

            if not schema_name:
                mapping_matrix.append(f"| {folder_name} | {file} | NONE | None |")
                orphaned_files.append(rel_path)
                continue

            mapping_matrix.append(f"| {folder_name} | {file} | {schema_name} | {confidence} |")
            data_registry.append({"schema": schema_name, "data": data})

            # Validate
            try:
                schema = schemas_by_name[schema_name]
                # We need the validator to know the Base URI of the root schema
                # so it can resolve relative refs inside it against the registry

                full_schema_path = os.path.join(SCHEMAS_DIR, schema_name)
                base_uri = Path(full_schema_path).as_uri()

                # Check for $id in schema, if present referencing uses it.
                # But we constructed registry with file URIs.
                # If schema has NO $id, we might need to rely on the fact that we passed `base_uri`?

                # referencing + jsonschema pattern:
                ValidatorClass = validators.validator_for(schema)
                # Create validator with registry
                validator = ValidatorClass(schema, registry=registry)

                # We need to tell the validator the resolution scope (base URI) of the instance schema
                # Usually done via resolver, but with referencing?
                # We can wrap the schema in a Resource?

                # Actually, simpler:
                # validator.validate(data) works if schema references are absolute or matching registry keys.
                # But our schemas use relative refs: "definitions/core.schema.json"
                # This needs to be resolved relative to "file:///.../spells.schema.json"

                # With `referencing`, we need to look up the resource by URI to get the correct context?
                # Or we can verify if `Validator` handles the base URI.

                # Workaround: Manually resolve the root schema from registry to get a "Resolver" context?
                # No, that's overcomplicating.

                # Let's try attempting validation.
                # If it fails with "Unresolvable", we know we need to fix relative ref handling.
                # One trick: modify the schema object to include matching $id?
                # Or just rely on `resolver` argument which is still supported but wraps registry?

                # Standard modern way:
                # validation is contextual.
                # We can use `validator.validate(data)` but check if we need to set a base URI.
                # In strict mode, if references are relative, the schema MUST have an identifier or be loaded with one.

                # Let's try adding $id dynamically if missing?
                if "$id" not in schema:
                    schema["$id"] = base_uri

                # Re-create validator with updated schema
                # Update registry?
                # Registry is immutable.
                resource = Resource.from_contents(schema)  # parses $id
                registry_updated = registry.with_resource(base_uri, resource)

                validator = ValidatorClass(schema, registry=registry_updated)
                validator.validate(data)

            except ValidationError as e:
                path_str = ".".join([str(p) for p in e.path]) if e.path else "root"
                msg = e.message
                if len(msg) > 200:
                    msg = msg[:200] + "..."
                validation_failures.append(f"File `{rel_path}` vs `{schema_name}`: Field `{path_str}` - {msg}")
            except Exception as e:
                validation_failures.append(f"File `{rel_path}`: Runtime Error - {str(e)}")

    # 3. Consistency Check (Z-Score Outliers)
    numeric_fields = defaultdict(list)
    outliers = []

    for entry in data_registry:
        schema = entry["schema"]
        data = entry["data"]
        entity_id = data.get("entity_id", "unknown")

        # Flatten numeric fields
        for k, v in data.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_fields[f"{schema}::{k}"].append((entity_id, v))
            # Nested mechanics check
            if k == "mechanics" and isinstance(v, dict):
                for mk, mv in v.items():
                    if isinstance(mv, (int, float)) and not isinstance(mv, bool):
                        numeric_fields[f"{schema}::mechanics.{mk}"].append((entity_id, mv))

    for field_key, values in numeric_fields.items():
        if len(values) < 4:
            continue  # Need enough data points

        nums = [v[1] for v in values]
        if len(set(nums)) == 1:
            continue  # All same value

        mean = statistics.mean(nums)
        stdev = statistics.stdev(nums)
        if stdev == 0:
            continue

        for entity_id, val in values:
            z_score = (val - mean) / stdev
            if abs(z_score) > 3.0:
                schema_name, field_name = field_key.split("::")
                outliers.append(
                    f"Schema `{schema_name}`: Field `{field_name}` has value `{val}` in `{entity_id}` (Z-Score: {z_score:.2f}, Mean: {mean:.2f})"
                )

    # 4. Orphaned Schemas
    used_schemas = set([x["schema"] for x in data_registry])
    # Registry keys are full URIs, we need to map back to filenames or use schemas_by_name keys
    all_schemas = set(schemas_by_name.keys())
    # Normalize used_schemas to match schemas_by_name keys if needed
    # used_schemas are already keys from schemas_by_name (see Mapping logic)
    orphaned_schemas = list(all_schemas - used_schemas)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Audit Report V2\n\n")
        f.write("## Validation Failures\n")
        if validation_failures:
            for fail in validation_failures:
                f.write(f"- {fail}\n")
        else:
            f.write("None.\n")

        f.write("\n## Consistency Outliers (Z-Score > 3.0)\n")
        if outliers:
            for o in outliers:
                f.write(f"- {o}\n")
        else:
            f.write("No statistical outliers detected.\n")

        f.write("\n## Orphaned Schemas\n")
        if orphaned_schemas:
            for s in orphaned_schemas:
                f.write(f"- {s}\n")
        else:
            f.write("No orphaned schemas.\n")

        f.write("\n## Mapping\n")
        for m in mapping_matrix:
            f.write(m + "\n")


if __name__ == "__main__":
    main()
