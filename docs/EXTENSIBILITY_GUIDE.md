# API Extensibility & Field Management

## Executive Summary: "Strict but Safe"

Adding or changing fields in this API is **Moderately Difficult** by design. You cannot simply add a field to a JSON data file; the build system will reject it.

**Why?**

- **Schema Strictness:** All schemas use `"unevaluatedProperties": false` (or `additionalProperties: false`). This means any field not explicitly defined in the schema is treated as an error.
- **Validation at Build Time:** `build_api.py` runs `validate_integrity.py`, which validates every single data file against its schema.
- **Type Safety:** The system enforces types (string, integer, enum) rigorously.

## How to Add a New Field

To add a field (e.g., `mana_cost` to a Hero), you must follow this sequence:

### 1. Update the Schema (`schemas/v2/`)

Locate the relevant schema file (e.g., `schemas/v2/heroes.schema.json`).
Add the property definition:

```json
"properties": {
  "mana_cost": {
    "type": "integer",
    "minimum": 0,
    "description": "Mana required to summon this hero."
  }
}
```

### 2. Update the Data (`data/`)

Now you can add the field to your JSON files in `data/heroes/`.

```json
{
  "entity_id": "archmage",
  "mana_cost": 100,
  ...
}
```

### 3. Verify

Run the build script to confirm everything is correct:

```shell
python scripts/build_api.py
```

## How to Change a Field (Breaking Change)

Changing a field (e.g., renaming `cost` to `gold_cost`) is harder because it breaks backward compatibility.

1.  **Modify Schema:** Update the schema to accept _both_ the old and new field (optional) or just the new one.
2.  **Migrate Data:** You may need to write a migration script (like `migrate_v2.py`) to batch-update all JSON files.
3.  **Strict Mode:** Once migrated, remove the old field from the schema to enforce the new structure.

## Comparison: V2 vs. Legacy V1

The user experience of extending the API has shifted from "Quick & Dirty" to "Structured & Safe".

| Feature             | Legacy V1                                                            | Current V2                                                                            |
| :------------------ | :------------------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| **Data Structure**  | **Monolithic:** One giant `all_data.json` file.                      | **Granular:** One file per entity (e.g., `data/heroes/archmage.json`).                |
| **Adding Fields**   | **Easy but Dangerous:** You could just type a new key into the JSON. | **Strict:** You _must_ update the Schema first, or the build fails.                   |
| **Validation**      | Loose or nonexistent. "It works if the game loads."                  | **Strict & CI-Gated:** `unevaluatedProperties: false` ensures 100% schema compliance. |
| **Merge Conflicts** | **Nightmare:** Two people editing `all_data.json` caused conflicts.  | **Trivial:** editing different files causes no conflicts.                             |
| **Safety**          | Low. Typo in one object breaks the whole API.                        | High. Typo in one file is isolated and caught by `build_api.py`.                      |

**Verdict:** V2 is "harder" because it forces you to be deliberate (Schema -> Data -> Build), but it eliminates the "silent failures" and "data rot" that plagued V1.
