import json
import glob
from collections import Counter

files = glob.glob(r"..\backend\data\fhir\*.json")

codes = Counter()
displays = {}

print("Scanning observation codes...")
print("Files:", len(files))
print()

for i, filepath in enumerate(files, 1):

    with open(filepath, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Observation":
            continue

        code_data = resource.get("code", {})

        for coding in code_data.get("coding", []):
            code = coding.get("code")

            if code:
                codes[code] += 1
                displays[code] = coding.get("display", "")

        # Also inspect component codes
        for component in resource.get("component", []):
            component_code = component.get("code", {})

            for coding in component_code.get("coding", []):
                code = coding.get("code")

                if code:
                    codes[code] += 1
                    displays[code] = coding.get("display", "")

    if i % 100 == 0:
        print(f"Processed {i}/{len(files)} files")

print()
print("=" * 90)
print("MOST COMMON OBSERVATION CODES")
print("=" * 90)

for code, count in codes.most_common(100):
    print(f"{code:15} {count:8}  {displays.get(code, '')}")

print()
print("=" * 90)
print("IMPORTANT CODES")
print("=" * 90)

important = [
    "8302-2",
    "29463-7",
    "39156-5",
    "55284-4",
    "8462-4",
    "8480-6",
    "2339-0",
    "4548-4",
    "2085-9",
    "2089-1",
    "2093-3",
    "2571-8",
    "8867-4",
]

for code in important:
    print(f"{code:15} {codes.get(code, 0):8}  {displays.get(code, 'NOT FOUND')}")

print()
print("DONE")