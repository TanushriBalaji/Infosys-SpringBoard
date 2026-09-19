import json
import glob
from collections import Counter

files = glob.glob(r"backend\data\fhir\*.json")

conditions = Counter()
codes = {}

print("Scanning FHIR files...")
print("Total files:", len(files))

for i, filepath in enumerate(files, 1):

    with open(filepath, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Condition":
            continue

        code_data = resource.get("code", {})

        # Prefer condition text
        name = code_data.get("text")

        # Otherwise use coding display
        coding = code_data.get("coding", [])

        if not name and coding:
            name = coding[0].get("display")

        if not name:
            name = "UNKNOWN"

        conditions[name] += 1

        if coding:
            codes[name] = coding[0].get("code", "NO_CODE")

    if i % 100 == 0:
        print(f"Processed {i}/{len(files)} files")

print()
print("CONDITIONS FOUND:", sum(conditions.values()))
print("=" * 80)

for name, count in conditions.most_common(50):
    print(f"{name[:60]:60} {count:6}  code={codes.get(name, 'NO_CODE')}")

print()
print("DONE")