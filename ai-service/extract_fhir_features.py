import json
import glob
from pathlib import Path
from datetime import datetime
import pandas as pd


# ============================================================
# MEDISPHERE FHIR → ML FEATURE EXTRACTION
# Targets:
#   1. Diabetes
#   2. Cardiovascular Disease (CVD)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FHIR_DIR = BASE_DIR.parent / "backend" / "data" / "fhir"

OUTPUT_FILE = BASE_DIR / "fhir_features.csv"


# ============================================================
# LOINC CODES
# ============================================================

CODES = {
    "height_cm": "8302-2",
    "weight_kg": "29463-7",
    "bmi": "39156-5",

    "systolic_bp": "8480-6",
    "diastolic_bp": "8462-4",

    "glucose": "2339-0",
    "hba1c": "4548-4",

    "hdl_cholesterol": "2085-9",
    "total_cholesterol": "2093-3",
    "triglycerides": "2571-8",

    "creatinine": "38483-4",
    "calcium": "49765-1",
    "sodium": "2947-0",
    "potassium": "6298-4",
}


# ============================================================
# DISEASE CODES
# ============================================================

# Diabetes
DIABETES_CODE = "44054006"


# Cardiovascular disease conditions found
# in the actual MediSphere FHIR dataset.

CVD_CODES = {
    "53741008": "Coronary Heart Disease",
    "88805009": "Chronic congestive heart failure",
    "49436004": "Atrial Fibrillation",
    "410429000": "Cardiac Arrest",
    "429007001": "History of cardiac arrest",
    "22298006": "Myocardial Infarction",
    "399211009": "History of myocardial infarction",
}


# ============================================================
# HELPERS
# ============================================================

def get_numeric_value(resource):
    """
    Extract valueQuantity.value from an Observation.
    """

    value_quantity = resource.get("valueQuantity")

    if value_quantity:

        value = value_quantity.get("value")

        if isinstance(value, (int, float)):
            return float(value)

    return None


def calculate_age(birth_date):

    if not birth_date:
        return None

    try:

        birth = datetime.strptime(
            birth_date[:10],
            "%Y-%m-%d"
        )

        today = datetime.now()

        age = today.year - birth.year

        if (today.month, today.day) < (
            birth.month,
            birth.day
        ):
            age -= 1

        return age

    except Exception:

        return None


# ============================================================
# FIND FHIR FILES
# ============================================================

files = glob.glob(
    str(FHIR_DIR / "*.json")
)


print("=" * 70)
print("MEDISPHERE FHIR FEATURE EXTRACTION")
print("=" * 70)

print()
print("FHIR directory:")
print(FHIR_DIR)

print()
print("JSON files:", len(files))
print()


# ============================================================
# STORAGE
# ============================================================

patients = {}

diabetes_condition_count = 0

cvd_condition_count = 0

error_count = 0


# ============================================================
# PROCESS FILES
# ============================================================

for file_index, filepath in enumerate(files, 1):

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            bundle = json.load(f)


        patient = None

        observations = []

        has_diabetes = False

        has_cvd = False


        # ====================================================
        # READ RESOURCES
        # ====================================================

        for entry in bundle.get("entry", []):

            resource = entry.get(
                "resource",
                {}
            )

            resource_type = resource.get(
                "resourceType"
            )


            # ------------------------------------------------
            # PATIENT
            # ------------------------------------------------

            if resource_type == "Patient":

                patient = resource


            # ------------------------------------------------
            # OBSERVATION
            # ------------------------------------------------

            elif resource_type == "Observation":

                observations.append(resource)


            # ------------------------------------------------
            # CONDITION
            # ------------------------------------------------

            elif resource_type == "Condition":

                code_data = resource.get(
                    "code",
                    {}
                )

                for coding in code_data.get(
                    "coding",
                    []
                ):

                    code = coding.get("code")

                    if not code:
                        continue


                    # ------------------------------
                    # DIABETES
                    # ------------------------------

                    if code == DIABETES_CODE:

                        has_diabetes = True

                        diabetes_condition_count += 1


                    # ------------------------------
                    # CVD
                    # ------------------------------

                    if code in CVD_CODES:

                        has_cvd = True

                        cvd_condition_count += 1


        # ====================================================
        # PATIENT CHECK
        # ====================================================

        if not patient:

            continue


        patient_id = patient.get("id")


        # ====================================================
        # DEMOGRAPHICS
        # ====================================================

        age = calculate_age(
            patient.get("birthDate")
        )


        gender = patient.get(
            "gender",
            "unknown"
        )


        if gender == "male":

            gender_value = 1

        elif gender == "female":

            gender_value = 0

        else:

            gender_value = -1


        # ====================================================
        # INITIALIZE FEATURES
        # ====================================================

        features = {}

        for feature_name in CODES:

            features[feature_name] = None


        # ====================================================
        # PROCESS OBSERVATIONS
        # ====================================================

        for observation in observations:

            # ----------------------------------------------
            # TOP LEVEL CODE
            # ----------------------------------------------

            coding_list = (
                observation
                .get("code", {})
                .get("coding", [])
            )


            observation_codes = []

            for coding in coding_list:

                code = coding.get("code")

                if code:

                    observation_codes.append(code)


            # ----------------------------------------------
            # NORMAL OBSERVATION VALUE
            # ----------------------------------------------

            value = get_numeric_value(
                observation
            )


            if value is not None:

                for feature_name, expected_code in CODES.items():

                    if expected_code in observation_codes:

                        features[feature_name] = value


            # ----------------------------------------------
            # COMPONENT VALUES
            # ----------------------------------------------

            for component in observation.get(
                "component",
                []
            ):

                component_codings = (
                    component
                    .get("code", {})
                    .get("coding", [])
                )


                component_codes = []

                for coding in component_codings:

                    code = coding.get("code")

                    if code:

                        component_codes.append(code)


                component_value = (
                    component
                    .get("valueQuantity", {})
                    .get("value")
                )


                if not isinstance(
                    component_value,
                    (int, float)
                ):

                    continue


                component_value = float(
                    component_value
                )


                # ------------------------------------------
                # SYSTOLIC BP
                # ------------------------------------------

                if CODES["systolic_bp"] in component_codes:

                    features["systolic_bp"] = component_value


                # ------------------------------------------
                # DIASTOLIC BP
                # ------------------------------------------

                if CODES["diastolic_bp"] in component_codes:

                    features["diastolic_bp"] = component_value


        # ====================================================
        # CREATE PATIENT ROW
        # ====================================================

        row = {

            "patient_id": patient_id,

            "age": age,

            "gender": gender_value,

            "height_cm": features["height_cm"],

            "weight_kg": features["weight_kg"],

            "bmi": features["bmi"],

            "systolic_bp": features["systolic_bp"],

            "diastolic_bp": features["diastolic_bp"],

            "glucose": features["glucose"],

            "hba1c": features["hba1c"],

            "hdl_cholesterol": features["hdl_cholesterol"],

            "total_cholesterol": features["total_cholesterol"],

            "triglycerides": features["triglycerides"],

            "creatinine": features["creatinine"],

            "calcium": features["calcium"],

            "sodium": features["sodium"],

            "potassium": features["potassium"],

            # ------------------------------------------
            # TARGET 1: DIABETES
            # ------------------------------------------

            "diabetes": 1 if has_diabetes else 0,

            # ------------------------------------------
            # TARGET 2: CVD
            # ------------------------------------------

            "cvd": 1 if has_cvd else 0,

        }


        patients[patient_id] = row


        # ====================================================
        # PROGRESS
        # ====================================================

        if file_index % 100 == 0:

            print(
                f"Processed {file_index}/{len(files)} files"
            )


    except Exception as e:

        error_count += 1

        print()
        print("ERROR:")
        print(filepath)
        print(e)


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(
    list(patients.values())
)


# ============================================================
# SAVE CSV
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("EXTRACTION COMPLETE")
print("=" * 70)

print(
    "Patients extracted:",
    len(df)
)


print()
print("DIABETES TARGET")
print("-" * 70)

print(
    "Diabetes positive:",
    int(df["diabetes"].sum())
)

print(
    "No diabetes:",
    int((df["diabetes"] == 0).sum())
)


print()
print("CVD TARGET")
print("-" * 70)

print(
    "CVD positive:",
    int(df["cvd"].sum())
)

print(
    "No CVD:",
    int((df["cvd"] == 0).sum())
)


print()
print("FEATURES")
print("-" * 70)

for column in df.columns:

    print(
        f"{column:25} missing={df[column].isna().sum()}"
    )


print()
print(
    "Diabetes Condition records:",
    diabetes_condition_count
)


print(
    "CVD Condition records:",
    cvd_condition_count
)


print(
    "Files with errors:",
    error_count
)


print()
print("Saved to:")
print(OUTPUT_FILE)

print("=" * 70)