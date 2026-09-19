import json
import glob
from collections import Counter

files = glob.glob(r"backend\data\fhir\*.json")

print("JSON FILES:", len(files))

resource_counts = Counter()
error_count = 0

for filepath in files:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            bundle = json.load(f)

        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            if resource_type:
                resource_counts[resource_type] += 1

    except Exception as e:
        error_count += 1

print("\nRESOURCE TYPES")
print("=" * 40)

for resource_type, count in sorted(resource_counts.items()):
    print(f"{resource_type:30} {count}")

print("\nFILES WITH ERRORS:", error_count)