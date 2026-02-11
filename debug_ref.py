import json
import os
from jsonschema import RefResolver

path = 'c:/Projects/spellcasters-community-api/schemas/v2/definitions/stats.schema.json'
with open(path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

print(f"Loaded schema keys: {list(schema.keys())}")
if 'definitions' in schema:
    print(f"Definitions keys: {list(schema['definitions'].keys())}")
else:
    print("ERROR: No definitions key found!")

uri = 'file:///' + path.replace('\\', '/')
print(f"Base URI: {uri}")

resolver = RefResolver(uri, schema)

try:
    print("Attempting to resolve #/definitions/base_stats...")
    uri, resolved = resolver.resolve('#/definitions/base_stats')
    print("Resolved successfully!")
    print(resolved.keys())
except Exception as e:
    print(f"Failed to resolve: {e}")
