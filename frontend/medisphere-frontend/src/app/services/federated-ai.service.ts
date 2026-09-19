import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface FederatedStatus {
  status: string;
  model_loaded: boolean;
  model: string;
  hospitals: number;
  trees_per_hospital: number;
  global_trees: number;
  target: string;
  target_code: string;
  message?: string;
}

export interface HospitalResult {
  hospital: number;
  patients: number;
  diabetes_positive: number;
  diabetes_negative: number;
  local_trees: number;
  status: string;
}

export interface HospitalsResponse {
  hospital_count: number;
  hospitals: HospitalResult[];
  aggregation: string;
  global_trees: number;
}

export interface GlobalMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
}

export interface FederatedResults {
  dataset: {
    total_patients: number;
    diabetes_positive: number;
    diabetes_negative: number;
  };
  split: {
    test_size: number;
    training_patients: number;
    testing_patients: number;
    training_diabetes: number;
    testing_diabetes: number;
  };
  federated_learning: {
    hospitals: number;
    local_trees_per_hospital: number;
    global_trees: number;
    aggregation: string;
  };
  global_metrics: GlobalMetrics;
  confusion_matrix: number[][];
  hospitals: HospitalResult[];
  feature_importance: Array<{
    feature: string;
    importance: number;
  }>;
}

export interface FederatedPredictionRequest {
  age: number;
  gender: number;
  height_cm: number;
  weight_kg: number;
  bmi: number;
  systolic_bp: number;
  diastolic_bp: number;
  glucose: number;
  hba1c: number;
  hdl_cholesterol: number;
  total_cholesterol: number;
  triglycerides: number;
  creatinine: number;
  calcium: number;
  sodium: number;
  potassium: number;
}

export interface FederatedPredictionResponse {
  prediction: number;
  condition: string;
  probability: number;
  risk_percentage: number;
  risk_category: string;
  model: string;
  hospitals: number;
  global_trees: number;
}

@Injectable({ providedIn: 'root' })
export class FederatedAiService {
  private apiUrl = 'http://localhost:5001/api/federated';
  constructor(private http: HttpClient) {}
  getStatus(): Observable<FederatedStatus> { return this.http.get<FederatedStatus>(`${this.apiUrl}/status`); }
  getHospitals(): Observable<HospitalsResponse> { return this.http.get<HospitalsResponse>(`${this.apiUrl}/hospitals`); }
  getResults(): Observable<FederatedResults> { return this.http.get<FederatedResults>(`${this.apiUrl}/results`); }
  getFeatures(): Observable<any> { return this.http.get<any>(`${this.apiUrl}/features`); }
  getTestResults(): Observable<any> { return this.http.get<any>(`${this.apiUrl}/test`); }
  predict(patientData: FederatedPredictionRequest): Observable<FederatedPredictionResponse> {
    return this.http.post<FederatedPredictionResponse>(`${this.apiUrl}/predict`, patientData);
  }
}
