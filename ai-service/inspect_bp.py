import json
import glob
import pprint

files = glob.glob(r"..\backend\data\fhir\*.json")

found = False

for filepath in files:

    with open(filepath, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    for entry in bundle.get("entry", []):

        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Observation":
            continue

        codes = []

        for coding in resource.get("code", {}).get("coding", []):
            codes.append(coding.get("code"))

        if "55284-4" in codes or "8480-6" in codes or "8462-4" in codes:

            print("=" * 80)
            print("FILE:", filepath)
            print("OBSERVATION ID:", resource.get("id"))
            print("=" * 80)

            pprint.pp(resource)

            found = True
            break

    if found:
        break

if not found:
    print("No blood pressure observation found.")