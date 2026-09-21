import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface RiskPrediction {
  patient_id?: string | null;
  predictions: {
    cvd: {
      probability: number;
      percentage: number;
      risk_level: string;
    };
    diabetes: {
      probability: number;
      percentage: number;
      risk_level: string;
    };
  };
  model: {
    type: string;
    hospitals: number;
    trees: number;
  };
}

export interface AiHealth {
  status: string;
  cvd_model_loaded: boolean;
  diabetes_model_loaded: boolean;
  model_directory?: string;
  error?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class RiskPredictionService {

  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getHealth(): Observable<AiHealth> {
    return this.http.get<AiHealth>(`${this.apiUrl}/health`);
  }

  predict(patientData: any): Observable<RiskPrediction> {
    return this.http.post<RiskPrediction>(
      `${this.apiUrl}/predict`,
      patientData
    );
  }
}
