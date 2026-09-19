from pathlib import Path
from datetime import datetime
import json

import joblib
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================
# MEDISPHERE AI SERVICE
# Federated Random Forest Prediction API
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_FILE = (
    BASE_DIR
    / "models"
    / "federated_random_forest.joblib"
)

METRICS_FILE = (
    BASE_DIR
    / "models"
    / "federated_metrics.json"
)


# ============================================================
# FEATURE ORDER
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


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

print()
print("=" * 70)
print("MEDISPHERE AI SERVICE")
print("=" * 70)

print()
print("Loading federated model:")
print(MODEL_FILE)


try:

    saved_model = joblib.load(
        MODEL_FILE
    )

    MODEL = saved_model["model"]

    IMPUTER = saved_model["imputer"]

    MODEL_METADATA = saved_model

    print("Model loaded successfully.")

    print(
        "Hospitals:",
        saved_model["num_hospitals"]
    )

    print(
        "Trees per hospital:",
        saved_model["local_trees"]
    )

    print(
        "Global trees:",
        saved_model["global_trees"]
    )

except Exception as e:

    MODEL = None

    IMPUTER = None

    MODEL_METADATA = {}

    print()
    print("MODEL LOAD ERROR")
    print(e)


# ============================================================
# LOAD METRICS
# ============================================================

if METRICS_FILE.exists():

    try:

        with open(
            METRICS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            TRAINING_METRICS = json.load(f)

    except Exception:

        TRAINING_METRICS = {}

else:

    TRAINING_METRICS = {}


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(

    title="MediSphere Federated AI Service",

    description=(
        "Federated Random Forest service "
        "for diabetes risk prediction."
    ),

    version="1.0.0"

)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


# ============================================================
# REQUEST MODEL
# ============================================================

class PatientData(BaseModel):

    age: float | None = None

    gender: float | None = None

    height_cm: float | None = None

    weight_kg: float | None = None

    bmi: float | None = None

    systolic_bp: float | None = None

    diastolic_bp: float | None = None

    glucose: float | None = None

    hba1c: float | None = None

    hdl_cholesterol: float | None = None

    total_cholesterol: float | None = None

    triglycerides: float | None = None

    creatinine: float | None = None

    calcium: float | None = None

    sodium: float | None = None

    potassium: float | None = None


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "service": "MediSphere Federated AI",

        "status": "running",

        "model": "Federated Random Forest",

        "target": "Diabetes",

        "endpoint": "/api/federated/predict"

    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/federated/status")
def status():

    if MODEL is None:

        return {

            "status": "error",

            "model_loaded": False,

            "message": "Federated model could not be loaded."

        }


    return {

        "status": "running",

        "model_loaded": True,

        "model": "Federated Random Forest",

        "hospitals": MODEL_METADATA.get(
            "num_hospitals",
            3
        ),

        "trees_per_hospital": MODEL_METADATA.get(
            "local_trees",
            50
        ),

        "global_trees": MODEL_METADATA.get(
            "global_trees",
            150
        ),

        "target": "Diabetes",

        "target_code": "44054006"

    }


# ============================================================
# FEDERATED LEARNING INFORMATION
# ============================================================

@app.get("/api/federated/hospitals")
def hospitals():

    hospitals_data = []

    hospital_info = TRAINING_METRICS.get(
        "hospitals",
        []
    )


    for hospital in hospital_info:

        hospitals_data.append({

            "hospital": hospital.get(
                "hospital"
            ),

            "patients": hospital.get(
                "patients"
            ),

            "diabetes_positive": hospital.get(
                "diabetes_positive"
            ),

            "diabetes_negative": hospital.get(
                "diabetes_negative"
            ),

            "local_trees": hospital.get(
                "local_trees"
            ),

            "status": "trained"

        })


    return {

        "hospital_count": len(
            hospitals_data
        ),

        "hospitals": hospitals_data,

        "aggregation": (
            "Decision-tree aggregation"
        ),

        "global_trees": MODEL_METADATA.get(
            "global_trees",
            150
        )

    }


# ============================================================
# TRAINING RESULTS
# ============================================================

@app.get("/api/federated/results")
def results():

    if not TRAINING_METRICS:

        raise HTTPException(

            status_code=404,

            detail="Training metrics not found."

        )


    return TRAINING_METRICS


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

@app.get("/api/federated/features")
def features():

    importance = TRAINING_METRICS.get(
        "feature_importance",
        []
    )


    return {

        "features": importance

    }


# ============================================================
# PREDICTION
# ============================================================

@app.post("/api/federated/predict")
def predict(patient: PatientData):

    if MODEL is None:

        raise HTTPException(

            status_code=500,

            detail="Federated model is not loaded."

        )


    # --------------------------------------------------------
    # Convert request to dictionary
    # --------------------------------------------------------

    data = patient.model_dump()


    # --------------------------------------------------------
    # Create DataFrame in EXACT training order
    # --------------------------------------------------------

    row = {

        feature: data.get(feature)

        for feature in FEATURE_COLUMNS

    }


    X = pd.DataFrame(
        [row],
        columns=FEATURE_COLUMNS
    )


    # --------------------------------------------------------
    # Apply training-time imputer
    # --------------------------------------------------------

    X_imputed = IMPUTER.transform(
        X
    )


    # --------------------------------------------------------
    # Prediction probability
    # --------------------------------------------------------

    probability = float(

        MODEL.predict_proba(
            X_imputed
        )[0][1]

    )


    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    prediction = int(
        probability >= 0.50
    )


    # --------------------------------------------------------
    # Risk category
    # --------------------------------------------------------

    if probability >= 0.70:

        risk_category = "HIGH"

    elif probability >= 0.40:

        risk_category = "MEDIUM"

    else:

        risk_category = "LOW"


    # --------------------------------------------------------
    # Return response
    # --------------------------------------------------------

    return {

        "prediction": prediction,

        "condition": "Diabetes",

        "probability": round(
            probability,
            4
        ),

        "risk_percentage": round(
            probability * 100,
            2
        ),

        "risk_category": risk_category,

        "model": "Federated Random Forest",

        "hospitals": MODEL_METADATA.get(
            "num_hospitals",
            3
        ),

        "global_trees": MODEL_METADATA.get(
            "global_trees",
            150
        ),

        "timestamp": datetime.now().isoformat()

    }


# ============================================================
# SIMPLE TEST PREDICTION
# ============================================================

@app.get("/api/federated/test")
def test_prediction():

    sample = PatientData(

        age=55,

        gender=1,

        height_cm=170,

        weight_kg=85,

        bmi=29.4,

        systolic_bp=140,

        diastolic_bp=90,

        glucose=130,

        hba1c=6.5,

        hdl_cholesterol=45,

        total_cholesterol=210,

        triglycerides=180,

        creatinine=1.0,

        calcium=9.2,

        sodium=140,

        potassium=4.2

    )


    return predict(sample)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    print()
    print("=" * 70)
    print("MEDISPHERE FEDERATED AI SERVICE READY")
    print("=" * 70)

    if MODEL is not None:

        print(
            "Model status: LOADED"
        )

        print(
            "Global trees:",
            MODEL_METADATA.get(
                "global_trees",
                150
            )
        )

    else:

        print(
            "Model status: ERROR"
        )

    print()
    print(
        "API: http://127.0.0.1:5001"
    )

    print(
        "Docs: http://127.0.0.1:5001/docs"
    )

    print("=" * 70)