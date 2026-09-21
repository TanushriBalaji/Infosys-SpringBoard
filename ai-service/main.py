from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

CVD_MODEL_PATH = MODEL_DIR / "cvd_federated_random_forest.joblib"
DIABETES_MODEL_PATH = MODEL_DIR / "diabetes_federated_random_forest.joblib"


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


app = FastAPI(
    title="MediSphere AI Risk Prediction Service",
    version="1.0.0",
    description="CVD and Diabetes prediction service using trained federated Random Forest models.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PatientFeatures(BaseModel):
    patient_id: Optional[str] = None

    age: float
    gender: float = Field(default=0)

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None

    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None

    glucose: Optional[float] = None
    hba1c: Optional[float] = None

    hdl_cholesterol: Optional[float] = None
    total_cholesterol: Optional[float] = None
    triglycerides: Optional[float] = None

    creatinine: Optional[float] = None
    calcium: Optional[float] = None
    sodium: Optional[float] = None
    potassium: Optional[float] = None


def load_model(path: Path):
    if not path.exists():
        raise RuntimeError(f"Model file not found: {path}")

    return joblib.load(path)


# Load once when FastAPI starts.
# Use the same feature medians used during training.
# This keeps prediction-time missing-value handling consistent with training.
FEATURE_SOURCE_PATH = BASE_DIR / "fhir_features.csv"

try:
    training_features = pd.read_csv(FEATURE_SOURCE_PATH)

    missing_training_columns = [
        c for c in FEATURE_COLUMNS if c not in training_features.columns
    ]
    if missing_training_columns:
        raise RuntimeError(
            f"fhir_features.csv is missing columns: {missing_training_columns}"
        )

    FEATURE_MEDIANS = (
        training_features[FEATURE_COLUMNS]
        .apply(pd.to_numeric, errors="coerce")
        .median()
        .to_dict()
    )

    cvd_model = load_model(CVD_MODEL_PATH)
    diabetes_model = load_model(DIABETES_MODEL_PATH)
    MODELS_LOADED = True
    MODEL_ERROR = None
except Exception as exc:
    cvd_model = None
    diabetes_model = None
    MODELS_LOADED = False
    MODEL_ERROR = str(exc)


def build_feature_dataframe(patient: PatientFeatures) -> pd.DataFrame:
    data = {}

    for feature in FEATURE_COLUMNS:
        value = getattr(patient, feature)

        if value is None:
            data[feature] = FEATURE_MEDIANS.get(feature, 0.0)
        else:
            try:
                data[feature] = float(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Feature '{feature}' must be numeric or null."
                )

    return pd.DataFrame([data], columns=FEATURE_COLUMNS)


def get_probability(model, features: pd.DataFrame) -> float:
    probability = model.predict_proba(features)

    # Standard sklearn binary classifier output.
    if probability.ndim == 2:
        return float(probability[0, 1])

    return float(probability[0])


def risk_level(probability: float) -> str:
    if probability >= 0.70:
        return "HIGH"
    elif probability >= 0.40:
        return "MODERATE"
    else:
        return "LOW"


@app.get("/")
def root():
    return {
        "service": "MediSphere AI Risk Prediction Service",
        "status": "running",
        "models_loaded": MODELS_LOADED,
    }


@app.get("/health")
def health():
    return {
        "status": "UP" if MODELS_LOADED else "DOWN",
        "cvd_model_loaded": cvd_model is not None,
        "diabetes_model_loaded": diabetes_model is not None,
        "model_directory": str(MODEL_DIR),
        "error": MODEL_ERROR,
    }


@app.get("/models")
def models():
    return {
        "cvd_model": CVD_MODEL_PATH.name,
        "cvd_exists": CVD_MODEL_PATH.exists(),
        "diabetes_model": DIABETES_MODEL_PATH.name,
        "diabetes_exists": DIABETES_MODEL_PATH.exists(),
        "features": FEATURE_COLUMNS,
    }


@app.post("/predict")
def predict(patient: PatientFeatures):
    if not MODELS_LOADED:
        raise HTTPException(
            status_code=503,
            detail=f"AI models are not loaded: {MODEL_ERROR}",
        )

    try:
        features = build_feature_dataframe(patient)

        cvd_probability = get_probability(cvd_model, features)
        diabetes_probability = get_probability(diabetes_model, features)

        return {
            "patient_id": patient.patient_id,
            "predictions": {
                "cvd": {
                    "probability": round(cvd_probability, 4),
                    "percentage": round(cvd_probability * 100, 2),
                    "risk_level": risk_level(cvd_probability),
                },
                "diabetes": {
                    "probability": round(diabetes_probability, 4),
                    "percentage": round(diabetes_probability * 100, 2),
                    "risk_level": risk_level(diabetes_probability),
                },
            },
            "model": {
                "type": "Federated Random Forest",
                "hospitals": 3,
                "trees": 150,
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        )


@app.post("/predict/cvd")
def predict_cvd(patient: PatientFeatures):
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail=MODEL_ERROR)

    try:
        features = build_feature_dataframe(patient)
        probability = get_probability(cvd_model, features)

        return {
            "patient_id": patient.patient_id,
            "condition": "CVD",
            "probability": round(probability, 4),
            "percentage": round(probability * 100, 2),
            "risk_level": risk_level(probability),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/predict/diabetes")
def predict_diabetes(patient: PatientFeatures):
    if not MODELS_LOADED:
        raise HTTPException(status_code=503, detail=MODEL_ERROR)

    try:
        features = build_feature_dataframe(patient)
        probability = get_probability(diabetes_model, features)

        return {
            "patient_id": patient.patient_id,
            "condition": "Diabetes",
            "probability": round(probability, 4),
            "percentage": round(probability * 100, 2),
            "risk_level": risk_level(probability),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
