import json
import glob

print("=" * 70)
print("MEDISPHERE - CVD CONDITION INSPECTION")
print("=" * 70)

files = glob.glob("../backend/data/fhir/*.json")

seen = {}

for filepath in files:

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            bundle = json.load(f)

        for entry in bundle.get("entry", []):

            resource = entry.get("resource", {})

            if resource.get("resourceType") != "Condition":
                continue

            code_data = resource.get("code", {})

            for coding in code_data.get("coding", []):

                code = coding.get("code")
                display = coding.get("display", "")

                if not code:
                    continue

                text = display.lower()

                keywords = [
                    "coronary",
                    "heart failure",
                    "cardiac",
                    "myocardial infarction",
                    "heart disease",
                    "ischemic heart",
                    "ischaemic heart",
                    "cardiomyopathy",
                    "arrhythmia",
                    "atrial fibrillation",
                    "angina"
                ]

                if any(keyword in text for keyword in keywords):

                    key = (code, display)

                    if key not in seen:
                        seen[key] = 0

                    seen[key] += 1

    except Exception as e:

        print("Error:", filepath)
        print(e)


print()
print("=" * 70)
print("CARDIOVASCULAR CONDITIONS FOUND")
print("=" * 70)

for (code, display), count in sorted(
    seen.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"CODE: {code:20} "
        f"COUNT: {count:5} "
        f"NAME: {display}"
    )


print()
print("=" * 70)
print("DONE")
print("=" * 70)