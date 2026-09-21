import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
from sklearn.model_selection import train_test_split, StratifiedKFold

from federated_model import FederatedRandomForest


FEATURE_COLUMNS = [
    "age", "gender", "height_cm", "weight_kg", "bmi",
    "systolic_bp", "diastolic_bp", "glucose", "hba1c",
    "hdl_cholesterol", "total_cholesterol", "triglycerides",
    "creatinine", "calcium", "sodium", "potassium"
]

TARGET_COLUMN = "diabetes"
DATA_PATH = Path("fhir_features.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20
NUM_HOSPITALS = 3
LOCAL_TREES = 50


print("\n" + "=" * 80)
print("MEDISPHERE - Diabetes FEDERATED RANDOM FOREST")
print("=" * 80)

df = pd.read_csv(DATA_PATH)

required = FEATURE_COLUMNS + [TARGET_COLUMN]
missing_columns = [c for c in required if c not in df.columns]
if missing_columns:
    raise RuntimeError(f"Missing required columns: {missing_columns}")

df = df.dropna(subset=[TARGET_COLUMN]).reset_index(drop=True)

X = df[FEATURE_COLUMNS].copy()
y = df[TARGET_COLUMN].astype(int).copy()

print(f"Dataset shape: {df.shape}")
print(f"Patients: {len(df)}")
print(f"Diabetes positive: {int(y.sum())}")
print(f"No Diabetes: {int((y == 0).sum())}")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y
)

print("\n" + "=" * 80)
print("TRAIN / TEST SPLIT")
print("=" * 80)
print(f"Training patients: {len(X_train)}")
print(f"Testing patients: {len(X_test)}")
print(f"Training Diabetes: {int(y_train.sum())}")
print(f"Testing Diabetes: {int(y_test.sum())}")

imputer = SimpleImputer(strategy="median")
X_train_imputed = pd.DataFrame(
    imputer.fit_transform(X_train),
    columns=FEATURE_COLUMNS,
    index=X_train.index
)
X_test_imputed = pd.DataFrame(
    imputer.transform(X_test),
    columns=FEATURE_COLUMNS,
    index=X_test.index
)

print("Missing-value processing complete.")

# IMPORTANT:
# StratifiedKFold returns:
#   train_idx = 2/3 of the data
#   val_idx   = 1/3 of the data
#
# For simulated hospitals we need DISJOINT partitions.
# Therefore each hospital receives val_idx, not train_idx.
print("\n" + "=" * 80)
print("CREATING DISJOINT SIMULATED HOSPITAL DATASETS")
print("=" * 80)

skf = StratifiedKFold(
    n_splits=NUM_HOSPITALS,
    shuffle=True,
    random_state=RANDOM_STATE
)

hospital_datasets = []
all_assigned_positions = []

for hospital_number, (_, hospital_idx) in enumerate(
    skf.split(X_train_imputed, y_train), start=1
):
    hospital_X = X_train_imputed.iloc[hospital_idx].reset_index(drop=True)
    hospital_y = y_train.iloc[hospital_idx].reset_index(drop=True)

    hospital_datasets.append((hospital_X, hospital_y))
    all_assigned_positions.extend(hospital_idx.tolist())

    print(f"\nHOSPITAL {hospital_number}")
    print("-" * 50)
    print(f"Patients: {len(hospital_X)}")
    print(f"Diabetes positive: {int(hospital_y.sum())}")
    print(f"No Diabetes: {int((hospital_y == 0).sum())}")

# Hard correctness checks.
expected_positions = list(range(len(X_train_imputed)))

if len(all_assigned_positions) != len(expected_positions):
    raise RuntimeError(
        f"Hospital partition size is wrong: "
        f"assigned={len(all_assigned_positions)}, "
        f"expected={len(expected_positions)}"
    )

if len(set(all_assigned_positions)) != len(all_assigned_positions):
    raise RuntimeError(
        "Hospital partition contains overlapping patients."
    )

if sorted(all_assigned_positions) != expected_positions:
    raise RuntimeError(
        "Hospital partition does not cover every training patient exactly once."
    )

total_hospital_patients = sum(len(hx) for hx, _ in hospital_datasets)
total_hospital_positive = sum(int(hy.sum()) for _, hy in hospital_datasets)

if total_hospital_patients != len(X_train_imputed):
    raise RuntimeError(
        f"Hospital patient total mismatch: "
        f"{total_hospital_patients} != {len(X_train_imputed)}"
    )

if total_hospital_positive != int(y_train.sum()):
    raise RuntimeError(
        f"Hospital positive total mismatch: "
        f"{total_hospital_positive} != {int(y_train.sum())}"
    )

print("\n" + "=" * 80)
print("PARTITION CHECK PASSED")
print("=" * 80)
print(f"Total hospital patients: {total_hospital_patients}")
print(f"Total hospital Diabetes positive: {total_hospital_positive}")
print("Every training patient is assigned to exactly one hospital.")

# Train one local Random Forest at each simulated hospital.
local_models = []

print("\n" + "=" * 80)
print("LOCAL HOSPITAL TRAINING")
print("=" * 80)

for hospital_number, (hospital_X, hospital_y) in enumerate(
    hospital_datasets, start=1
):
    model = RandomForestClassifier(
        n_estimators=LOCAL_TREES,
        random_state=RANDOM_STATE + hospital_number,
        class_weight="balanced",
        max_features="sqrt",
        min_samples_leaf=2,
        n_jobs=-1
    )

    model.fit(hospital_X, hospital_y)
    local_models.append(model)

    print(
        f"Hospital {hospital_number} trained: "
        f"{len(hospital_X)} patients, "
        f"{int(hospital_y.sum())} positive"
    )

# Federated aggregation: collect all local trees into one global forest.
global_estimators = []
for model in local_models:
    global_estimators.extend(model.estimators_)

global_model = FederatedRandomForest(
    estimators=global_estimators,
    feature_names=FEATURE_COLUMNS,
    classes=[0, 1]
)

print("\n" + "=" * 80)
print("FEDERATED MODEL CREATED")
print("=" * 80)
print(f"Local hospitals: {NUM_HOSPITALS}")
print(f"Trees per hospital: {LOCAL_TREES}")
print(f"Global trees: {len(global_estimators)}")

# Evaluate on the completely held-out test set.
X_test_np = X_test_imputed.to_numpy()
y_test_np = y_test.to_numpy()

if hasattr(global_model, "predict_proba"):
    probabilities = global_model.predict_proba(X_test_np)[:, 1]
else:
    probabilities = np.asarray(global_model.predict_proba(X_test_np))[:, 1]

predictions = (probabilities >= 0.50).astype(int)

accuracy = accuracy_score(y_test_np, predictions)
precision = precision_score(y_test_np, predictions, zero_division=0)
recall = recall_score(y_test_np, predictions, zero_division=0)
f1 = f1_score(y_test_np, predictions, zero_division=0)
roc_auc = roc_auc_score(y_test_np, probabilities)
pr_auc = average_precision_score(y_test_np, probabilities)
cm = confusion_matrix(y_test_np, predictions)

print("\n" + "=" * 80)
print("TEST SET RESULTS")
print("=" * 80)
print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1       : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")
print(f"PR-AUC   : {pr_auc:.4f}")
print("\nConfusion Matrix:")
print(cm)

# Save the federated model.
model_filename = "diabetes_federated_random_forest.joblib"
metrics_filename = "diabetes_metrics.json"

model_path = MODEL_DIR / model_filename
metrics_path = MODEL_DIR / metrics_filename

joblib.dump(global_model, model_path)

metrics = {
    "model_type": "FederatedRandomForest",
    "target": TARGET_COLUMN,
    "dataset_patients": int(len(df)),
    "training_patients": int(len(X_train)),
    "testing_patients": int(len(X_test)),
    "training_positive": int(y_train.sum()),
    "testing_positive": int(y_test.sum()),
    "num_hospitals": NUM_HOSPITALS,
    "local_trees_per_hospital": LOCAL_TREES,
    "global_trees": len(global_estimators),
    "accuracy": float(accuracy),
    "precision": float(precision),
    "recall": float(recall),
    "f1": float(f1),
    "roc_auc": float(roc_auc),
    "pr_auc": float(pr_auc),
    "confusion_matrix": cm.tolist(),
    "features": FEATURE_COLUMNS
}

with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print("\n" + "=" * 80)
print("SAVED")
print("=" * 80)
print(f"Model  : {model_path}")
print(f"Metrics: {metrics_path}")
print("\nTRAINING COMPLETED SUCCESSFULLY.")
