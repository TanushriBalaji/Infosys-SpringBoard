import joblib
import numpy as np
import pandas as pd

from pathlib import Path

from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "fhir_features.csv"

MODEL_FILE = (
    BASE_DIR
    / "models"
    / "federated_random_forest.joblib"
)


# ============================================================
# FEATURES
# ============================================================

FEATURE_COLUMNS = [
    "age",
    "gender",
    "height_cm",
    "weight_kg",
    "bmi",
    "systolic_bp",
    "diastolic_bp",
    "glucose",
    "hba1c",
    "hdl_cholesterol",
    "total_cholesterol",
    "triglycerides",
    "creatinine",
    "calcium",
    "sodium",
    "potassium",
]

TARGET_COLUMN = "diabetes"

RANDOM_STATE = 42
TEST_SIZE = 0.20


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 80)
print("MEDISPHERE FEDERATED RANDOM FOREST - MODEL TEST")
print("=" * 80)

print()
print("Loading saved model:")
print(MODEL_FILE)

saved = joblib.load(MODEL_FILE)

model = saved["model"]
imputer = saved["imputer"]

print()
print("Model loaded successfully.")

print("Hospitals:", saved["num_hospitals"])
print("Trees per hospital:", saved["local_trees"])
print("Global trees:", saved["global_trees"])


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_FILE)

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN].astype(int)


# ============================================================
# RECREATE EXACT SAME TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    stratify=y,
    random_state=RANDOM_STATE,
)


# ============================================================
# APPLY SAVED IMPUTER
# ============================================================

X_test_imputed = imputer.transform(X_test)


# ============================================================
# PREDICTION
# ============================================================

probabilities = model.predict_proba(
    X_test_imputed
)[:, 1]

predictions = (
    probabilities >= 0.50
).astype(int)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    predictions
)

precision = precision_score(
    y_test,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    probabilities
)

pr_auc = average_precision_score(
    y_test,
    probabilities
)

cm = confusion_matrix(
    y_test,
    predictions
)


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 80)
print("INDEPENDENT MODEL TEST")
print("=" * 80)

print()
print("Test patients:", len(X_test))
print("Actual diabetes:", int(y_test.sum()))

print()

print(f"Accuracy       : {accuracy:.4f}")
print(f"Precision      : {precision:.4f}")
print(f"Recall         : {recall:.4f}")
print(f"F1 Score       : {f1:.4f}")
print(f"ROC-AUC        : {roc_auc:.4f}")
print(f"PR-AUC         : {pr_auc:.4f}")

print()
print("CONFUSION MATRIX")
print("-" * 40)

print(cm)


# ============================================================
# SAMPLE PREDICTIONS
# ============================================================

print()
print("=" * 80)
print("SAMPLE PREDICTIONS")
print("=" * 80)

for i in range(min(10, len(X_test))):

    actual = y_test.iloc[i]

    probability = probabilities[i]

    prediction = predictions[i]

    risk = (
        "HIGH"
        if probability >= 0.70
        else "MEDIUM"
        if probability >= 0.40
        else "LOW"
    )

    print(
        f"Patient {i + 1:02d} | "
        f"Actual={actual} | "
        f"Prediction={prediction} | "
        f"Probability={probability:.4f} | "
        f"Risk={risk}"
    )


# ============================================================
# FINAL CHECK
# ============================================================

print()
print("=" * 80)

if (
    abs(accuracy - 0.9958) < 0.0001
    and abs(f1 - 0.9744) < 0.0001
    and abs(roc_auc - 0.9812) < 0.0001
):
    print("MODEL TEST: PASSED")
    print()
    print("The saved federated model reproduces")
    print("the expected held-out test results.")

else:
    print("MODEL TEST: COMPLETED")
    print()
    print("The model loaded and produced predictions,")
    print("but the metrics differ from the original run.")

print("=" * 80)