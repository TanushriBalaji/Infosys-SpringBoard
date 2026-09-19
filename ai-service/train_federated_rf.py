import json
import joblib
import numpy as np
import pandas as pd

from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold
)

from federated_model import FederatedRandomForest


# ============================================================
# MEDISPHERE FEDERATED RANDOM FOREST
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "fhir_features.csv"

MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(exist_ok=True)

GLOBAL_MODEL_FILE = (
    MODEL_DIR / "federated_random_forest.joblib"
)

METRICS_FILE = (
    MODEL_DIR / "federated_metrics.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42

TEST_SIZE = 0.20

NUM_HOSPITALS = 3

LOCAL_TREES = 50


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
    "potassium"

]

TARGET_COLUMN = "diabetes"


# ============================================================
# LOAD DATA
# ============================================================

print()
print("=" * 80)
print("MEDISPHERE FEDERATED RANDOM FOREST")
print("=" * 80)

print()
print("Loading dataset:")
print(DATA_FILE)

df = pd.read_csv(DATA_FILE)

print()
print("Dataset shape:", df.shape)


# ============================================================
# VERIFY DATA
# ============================================================

required_columns = (
    FEATURE_COLUMNS +
    [TARGET_COLUMN]
)

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing columns: "
        + str(missing_columns)
    )


df = df.dropna(
    subset=[TARGET_COLUMN]
).copy()


X = df[FEATURE_COLUMNS].copy()

y = df[TARGET_COLUMN].astype(int).copy()


print()
print("Patients:", len(df))

print(
    "Diabetes positive:",
    int(y.sum())
)

print(
    "No diabetes:",
    int((y == 0).sum())
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=TEST_SIZE,

    stratify=y,

    random_state=RANDOM_STATE

)


print()
print("=" * 80)
print("TRAIN / TEST SPLIT")
print("=" * 80)

print(
    "Training patients:",
    len(X_train)
)

print(
    "Testing patients:",
    len(X_test)
)

print(
    "Training diabetes:",
    int(y_train.sum())
)

print(
    "Testing diabetes:",
    int(y_test.sum())
)


# ============================================================
# IMPUTATION
# ============================================================

print()
print("Preparing missing values...")

imputer = SimpleImputer(
    strategy="median"
)

X_train_imputed = imputer.fit_transform(
    X_train
)

X_test_imputed = imputer.transform(
    X_test
)

print("Missing-value processing complete.")


# ============================================================
# CREATE THREE SIMULATED HOSPITALS
# ============================================================

print()
print("=" * 80)
print("CREATING SIMULATED HOSPITAL DATASETS")
print("=" * 80)

skf = StratifiedKFold(

    n_splits=NUM_HOSPITALS,

    shuffle=True,

    random_state=RANDOM_STATE

)


hospital_datasets = []


for hospital_number, (
    indices,
    _
) in enumerate(
    skf.split(
        X_train_imputed,
        y_train
    ),
    start=1
):

    X_hospital = X_train_imputed[
        indices
    ]

    y_hospital = y_train.iloc[
        indices
    ].to_numpy()

    hospital_datasets.append(
        (
            X_hospital,
            y_hospital
        )
    )


# ============================================================
# LOCAL TRAINING
# ============================================================

print()
print("=" * 80)
print("LOCAL HOSPITAL TRAINING")
print("=" * 80)


local_forests = []

hospital_information = []


for hospital_number, (
    X_hospital,
    y_hospital
) in enumerate(
    hospital_datasets,
    start=1
):

    print()
    print("-" * 80)

    print(
        f"HOSPITAL {hospital_number}"
    )

    print("-" * 80)

    print(
        "Patients:",
        len(X_hospital)
    )

    print(
        "Diabetes positive:",
        int(y_hospital.sum())
    )

    print(
        "No diabetes:",
        int((y_hospital == 0).sum())
    )

    print()
    print(
        "Training local Random Forest..."
    )


    local_model = RandomForestClassifier(

        n_estimators=LOCAL_TREES,

        class_weight="balanced",

        random_state=(
            RANDOM_STATE +
            hospital_number
        ),

        n_jobs=-1,

        max_features="sqrt",

        min_samples_leaf=2

    )


    local_model.fit(
        X_hospital,
        y_hospital
    )


    print(
        "Local training complete."
    )

    print(
        "Local trees:",
        len(local_model.estimators_)
    )


    local_forests.append(
        local_model
    )


    hospital_information.append({

        "hospital": hospital_number,

        "patients": int(
            len(X_hospital)
        ),

        "diabetes_positive": int(
            y_hospital.sum()
        ),

        "diabetes_negative": int(
            (y_hospital == 0).sum()
        ),

        "local_trees": int(
            len(local_model.estimators_)
        )

    })


# ============================================================
# FEDERATED AGGREGATION
# ============================================================

print()
print("=" * 80)
print("FEDERATED AGGREGATION")
print("=" * 80)

print()
print(
    "Combining locally trained decision trees..."
)


global_estimators = []


for hospital_number, local_model in enumerate(
    local_forests,
    start=1
):

    print(
        f"Collecting trees from Hospital {hospital_number}..."
    )

    global_estimators.extend(
        local_model.estimators_
    )


print()

print(
    "Hospital count:",
    NUM_HOSPITALS
)

print(
    "Trees per hospital:",
    LOCAL_TREES
)

print(
    "Global tree count:",
    len(global_estimators)
)


# ============================================================
# CREATE GLOBAL MODEL
# ============================================================

global_model = FederatedRandomForest(

    estimators=global_estimators,

    feature_names=FEATURE_COLUMNS,

    classes=[0, 1]

)


# ============================================================
# TEST GLOBAL MODEL
# ============================================================

print()
print("=" * 80)
print("GLOBAL MODEL EVALUATION")
print("=" * 80)

print()
print(
    "Testing on untouched test data..."
)


y_probability = global_model.predict_proba(
    X_test_imputed
)[:, 1]


y_prediction = (
    y_probability >= 0.50
).astype(int)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_prediction
)

precision = precision_score(
    y_test,
    y_prediction,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_prediction,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_prediction,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

pr_auc = average_precision_score(
    y_test,
    y_probability
)

cm = confusion_matrix(
    y_test,
    y_prediction
)


# ============================================================
# PRINT RESULTS
# ============================================================

print()

print(
    f"Accuracy       : {accuracy:.4f}"
)

print(
    f"Precision      : {precision:.4f}"
)

print(
    f"Recall         : {recall:.4f}"
)

print(
    f"F1 Score       : {f1:.4f}"
)

print(
    f"ROC-AUC        : {roc_auc:.4f}"
)

print(
    f"PR-AUC         : {pr_auc:.4f}"
)


print()
print("CONFUSION MATRIX")
print("-" * 40)

print(cm)


print()
print("CLASSIFICATION REPORT")
print("-" * 80)

print(
    classification_report(
        y_test,
        y_prediction,
        target_names=[
            "No Diabetes",
            "Diabetes"
        ],
        zero_division=0
    )
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

feature_importance = (
    global_model.get_feature_importances()
)


importance_table = pd.DataFrame({

    "feature": FEATURE_COLUMNS,

    "importance": feature_importance

})


importance_table = importance_table.sort_values(
    "importance",
    ascending=False
)


print()
print("=" * 80)
print("TOP FEATURE IMPORTANCES")
print("=" * 80)


for _, row in importance_table.head(10).iterrows():

    print(
        f"{row['feature']:25} "
        f"{row['importance']:.6f}"
    )


# ============================================================
# SAVE MODEL
# ============================================================

print()
print("Saving global federated model...")


joblib.dump(

    {

        "model": global_model,

        "imputer": imputer,

        "feature_columns": FEATURE_COLUMNS,

        "target_column": TARGET_COLUMN,

        "classes": [0, 1],

        "num_hospitals": NUM_HOSPITALS,

        "local_trees": LOCAL_TREES,

        "global_trees": len(
            global_estimators
        ),

        "random_state": RANDOM_STATE

    },

    GLOBAL_MODEL_FILE

)


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {

    "dataset": {

        "total_patients": int(
            len(df)
        ),

        "diabetes_positive": int(
            y.sum()
        ),

        "diabetes_negative": int(
            (y == 0).sum()
        )

    },

    "split": {

        "test_size": TEST_SIZE,

        "training_patients": int(
            len(X_train)
        ),

        "testing_patients": int(
            len(X_test)
        ),

        "training_diabetes": int(
            y_train.sum()
        ),

        "testing_diabetes": int(
            y_test.sum()
        )

    },

    "federated_learning": {

        "hospitals": NUM_HOSPITALS,

        "local_trees_per_hospital": (
            LOCAL_TREES
        ),

        "global_trees": len(
            global_estimators
        ),

        "aggregation": (
            "Decision-tree aggregation"
        )

    },

    "global_metrics": {

        "accuracy": float(
            accuracy
        ),

        "precision": float(
            precision
        ),

        "recall": float(
            recall
        ),

        "f1": float(
            f1
        ),

        "roc_auc": float(
            roc_auc
        ),

        "pr_auc": float(
            pr_auc
        )

    },

    "confusion_matrix": cm.tolist(),

    "hospitals": hospital_information,

    "feature_importance": [

        {

            "feature": str(
                row["feature"]
            ),

            "importance": float(
                row["importance"]
            )

        }

        for _, row in importance_table.iterrows()

    ]

}


with open(
    METRICS_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 80)
print("FEDERATED RANDOM FOREST TRAINING COMPLETE")
print("=" * 80)

print()
print("Global model saved:")
print(GLOBAL_MODEL_FILE)

print()
print("Metrics saved:")
print(METRICS_FILE)

print()
print("Global trees:")
print(len(global_estimators))

print()
print("DONE")
print("=" * 80)