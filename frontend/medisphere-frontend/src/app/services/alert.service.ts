import { Injectable, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

export interface AlertRecord {
  alertId: string;
  patientId: string;
  alertType: string;
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  vitalName: string;
  vitalValue: number;
  threshold: string;
  message: string;
  timestamp: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
}

export interface VitalTelemetry {
  patientId: string;
  timestamp: string;
  heartRate: number;
  spo2: number;
  systolicBP: number;
  diastolicBP: number;
  temperature: number;
}

export interface RealtimeVitalRecord {
  id?: string;
  patientId: string;
  timestamp: string;
  heartRate: number;
  spo2: number;
  systolicBP: number;
  diastolicBP: number;
  temperature: number;
  status?: string;
}

export interface PatientSummary {
  id: string;
  name: string;
}

@Injectable({
  providedIn: 'root'
})
export class AlertService {
  private baseUrl = 'http://localhost:8080/api';

  private alertSubject = new Subject<AlertRecord>();
  private telemetrySubject = new Subject<VitalTelemetry>();
  private eventSource: EventSource | null = null;

  public alert$ = this.alertSubject.asObservable();
  public telemetry$ = this.telemetrySubject.asObservable();

  constructor(private http: HttpClient, private zone: NgZone) {}

  connectSse(): void {
    if (this.eventSource) {
      return;
    }

    this.eventSource = new EventSource(`${this.baseUrl}/alerts/stream`);

    this.eventSource.addEventListener('ALERT', (event: MessageEvent) => {
      this.zone.run(() => {
        try {
          const alert: AlertRecord = JSON.parse(event.data);
          this.alertSubject.next(alert);
        } catch (e) {
          console.error('Error parsing SSE alert payload:', e);
        }
      });
    });

    this.eventSource.addEventListener('TELEMETRY', (event: MessageEvent) => {
      this.zone.run(() => {
        try {
          const telemetry: VitalTelemetry = JSON.parse(event.data);
          this.telemetrySubject.next(telemetry);
        } catch (e) {
          console.error('Error parsing SSE telemetry payload:', e);
        }
      });
    });

    this.eventSource.onerror = (err) => {
      console.warn('SSE stream error, retrying connection...', err);
    };
  }

  disconnectSse(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  getAlerts(): Observable<AlertRecord[]> {
    return this.http.get<AlertRecord[]>(`${this.baseUrl}/alerts`);
  }

  acknowledgeAlert(id: string): Observable<AlertRecord> {
    return this.http.put<AlertRecord>(`${this.baseUrl}/alerts/${id}/acknowledge`, {});
  }

  resolveAlert(id: string): Observable<AlertRecord> {
    return this.http.put<AlertRecord>(`${this.baseUrl}/alerts/${id}/resolve`, {});
  }

  triggerAbnormal(patientId = 'P1001', condition = 'HIGH_HEART_RATE'): Observable<VitalTelemetry> {
    return this.http.post<VitalTelemetry>(`${this.baseUrl}/simulator/trigger-abnormal?patientId=${patientId}&condition=${condition}`, {});
  }

  getPatientList(): Observable<PatientSummary[]> {
    return this.http.get<PatientSummary[]>(`${this.baseUrl}/realtime-vitals/patients`);
  }

  getLatestVitals(patientId: string): Observable<RealtimeVitalRecord> {
    return this.http.get<RealtimeVitalRecord>(`${this.baseUrl}/realtime-vitals/patient/${encodeURIComponent(patientId)}/latest`);
  }

  getVitalsHistory(patientId: string): Observable<RealtimeVitalRecord[]> {
    return this.http.get<RealtimeVitalRecord[]>(`${this.baseUrl}/realtime-vitals/patient/${encodeURIComponent(patientId)}/history`);
  }

  selectSimulatorPatient(patientId: string): Observable<{ status: string; patientId: string }> {
    return this.http.post<{ status: string; patientId: string }>(`${this.baseUrl}/simulator/select-patient?patientId=${encodeURIComponent(patientId)}`, {});
  }

  getActiveSimulatorPatient(): Observable<{ activePatientId: string }> {
    return this.http.get<{ activePatientId: string }>(`${this.baseUrl}/simulator/active-patient`);
  }
}
