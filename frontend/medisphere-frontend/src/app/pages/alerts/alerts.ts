import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AlertService, AlertRecord, VitalTelemetry, PatientSummary, RealtimeVitalRecord } from '../../services/alert.service';

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './alerts.html',
  styleUrl: './alerts.css'
})
export class AlertsComponent implements OnInit, OnDestroy {

  alerts: AlertRecord[] = [];
  latestTelemetry: VitalTelemetry | null = null;
  heartRateHistory: number[] = [72, 75, 74, 78, 76, 75, 77, 79];

  patients: PatientSummary[] = [];
  selectedPatientId: string = '';
  selectedPatientName: string = '';
  filterByPatientOnly: boolean = false;

  loading = true;
  patientsLoading = false;
  error = '';
  actionMessage = '';

  private alertSub!: Subscription;
  private telemetrySub!: Subscription;

  constructor(private alertService: AlertService) {}

  ngOnInit(): void {
    this.loadPatients();
    this.loadAlerts();
    this.alertService.connectSse();

    this.alertSub = this.alertService.alert$.subscribe({
      next: (newAlert) => {
        console.log('Real-time SSE alert received:', newAlert);
        this.alerts = [newAlert, ...this.alerts.filter(a => a.alertId !== newAlert.alertId)];
        this.actionMessage = `NEW ALERT for ${newAlert.patientId}: ${newAlert.message}`;
      }
    });

    this.telemetrySub = this.alertService.telemetry$.subscribe({
      next: (telemetry) => {
        if (!this.selectedPatientId || telemetry.patientId === this.selectedPatientId) {
          this.latestTelemetry = telemetry;
          if (telemetry.heartRate) {
            this.heartRateHistory.push(Math.round(telemetry.heartRate));
            if (this.heartRateHistory.length > 25) {
              this.heartRateHistory.shift();
            }
          }
        }
      }
    });
  }

  ngOnDestroy(): void {
    if (this.alertSub) this.alertSub.unsubscribe();
    if (this.telemetrySub) this.telemetrySub.unsubscribe();
    this.alertService.disconnectSse();
  }

  loadPatients(): void {
    this.patientsLoading = true;
    this.alertService.getPatientList().subscribe({
      next: (list) => {
        this.patients = list;
        this.patientsLoading = false;

        // Fetch active patient from simulator
        this.alertService.getActiveSimulatorPatient().subscribe({
          next: (res) => {
            if (res.activePatientId && this.patients.some(p => p.id === res.activePatientId)) {
              this.selectedPatientId = res.activePatientId;
            } else if (this.patients.length > 0) {
              this.selectedPatientId = this.patients[0].id;
            }
            this.updateSelectedPatientName();
            this.loadPatientTelemetry(this.selectedPatientId);
          },
          error: () => {
            if (this.patients.length > 0) {
              this.selectedPatientId = this.patients[0].id;
              this.updateSelectedPatientName();
              this.loadPatientTelemetry(this.selectedPatientId);
            }
          }
        });
      },
      error: (err) => {
        console.error('Failed to load real patient list:', err);
        this.patientsLoading = false;
      }
    });
  }

  updateSelectedPatientName(): void {
    const found = this.patients.find(p => p.id === this.selectedPatientId);
    this.selectedPatientName = found ? found.name : this.selectedPatientId;
  }

  onPatientChange(): void {
    this.updateSelectedPatientName();
    this.loadPatientTelemetry(this.selectedPatientId);
    this.actionMessage = `Selected patient: ${this.selectedPatientName}. Click "Start Stream" to route wearable simulator to this patient.`;
  }

  startStreamForSelectedPatient(): void {
    if (!this.selectedPatientId) return;
    this.alertService.selectSimulatorPatient(this.selectedPatientId).subscribe({
      next: (res) => {
        this.actionMessage = `Wearable Simulator stream switched to patient: ${this.selectedPatientName} (${this.selectedPatientId})`;
      },
      error: (err) => {
        console.error('Failed to switch simulator patient:', err);
        this.actionMessage = 'Error switching simulator patient.';
      }
    });
  }

  loadPatientTelemetry(patientId: string): void {
    if (!patientId) return;

    this.alertService.getLatestVitals(patientId).subscribe({
      next: (vital) => {
        if (vital) {
          this.latestTelemetry = {
            patientId: vital.patientId,
            timestamp: vital.timestamp,
            heartRate: vital.heartRate,
            spo2: vital.spo2,
            systolicBP: vital.systolicBP,
            diastolicBP: vital.diastolicBP,
            temperature: vital.temperature
          };
        }
      },
      error: () => {
        // No previous vitals yet for this patient, simulator will produce soon
      }
    });

    this.alertService.getVitalsHistory(patientId).subscribe({
      next: (history) => {
        if (history && history.length > 0) {
          // Take heart rate values chronologically
          const hrs = [...history].reverse().map(h => Math.round(h.heartRate));
          this.heartRateHistory = hrs.slice(-25);
        }
      },
      error: () => {}
    });
  }

  get displayedAlerts(): AlertRecord[] {
    if (this.filterByPatientOnly && this.selectedPatientId) {
      return this.alerts.filter(a => a.patientId === this.selectedPatientId);
    }
    return this.alerts;
  }

  loadAlerts(): void {
    this.loading = true;
    this.alertService.getAlerts().subscribe({
      next: (data) => {
        this.alerts = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load alerts:', err);
        this.error = 'Unable to fetch historical alerts from backend.';
        this.loading = false;
      }
    });
  }

  acknowledgeAlert(alert: AlertRecord): void {
    this.alertService.acknowledgeAlert(alert.alertId).subscribe({
      next: () => {
        alert.status = 'ACKNOWLEDGED';
        this.actionMessage = `Alert ${alert.alertId} acknowledged.`;
      },
      error: (err) => console.error('Failed to acknowledge alert:', err)
    });
  }

  resolveAlert(alert: AlertRecord): void {
    this.alertService.resolveAlert(alert.alertId).subscribe({
      next: () => {
        alert.status = 'RESOLVED';
        this.actionMessage = `Alert ${alert.alertId} resolved.`;
      },
      error: (err) => console.error('Failed to resolve alert:', err)
    });
  }

  triggerAbnormalHeartRate(): void {
    const pId = this.selectedPatientId || 'urn:uuid:5cbc121b-cd71-4428-b8b7-31e53eba8184';
    this.actionMessage = `Triggering abnormal heart rate (145 bpm) for ${this.selectedPatientName || pId}...`;
    this.alertService.triggerAbnormal(pId, 'HIGH_HEART_RATE').subscribe({
      next: (res) => {
        console.log('Abnormal telemetry triggered:', res);
      },
      error: (err) => console.error('Failed to trigger abnormal telemetry:', err)
    });
  }

  triggerAbnormalBP(): void {
    const pId = this.selectedPatientId || 'urn:uuid:5cbc121b-cd71-4428-b8b7-31e53eba8184';
    this.actionMessage = `Triggering abnormal BP event (185 mmHg) for ${this.selectedPatientName || pId}...`;
    this.alertService.triggerAbnormal(pId, 'HIGH_BP').subscribe();
  }

  triggerLowSpo2(): void {
    const pId = this.selectedPatientId || 'urn:uuid:5cbc121b-cd71-4428-b8b7-31e53eba8184';
    this.actionMessage = `Triggering low SpO2 event (87%) for ${this.selectedPatientName || pId}...`;
    this.alertService.triggerAbnormal(pId, 'LOW_SPO2').subscribe();
  }

  getSeverityClass(severity: string): string {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MODERATE': return 'badge-moderate';
      default: return 'badge-low';
    }
  }

  getStatusClass(status: string): string {
    switch (status.toUpperCase()) {
      case 'ACTIVE': return 'status-active';
      case 'ACKNOWLEDGED': return 'status-ack';
      case 'RESOLVED': return 'status-resolved';
      default: return '';
    }
  }

  getSparklinePoints(): string {
    const width = 300;
    const height = 60;
    if (this.heartRateHistory.length < 2) return `0,${height/2} ${width},${height/2}`;

    const min = Math.min(...this.heartRateHistory, 60);
    const max = Math.max(...this.heartRateHistory, 150);
    const range = Math.max(max - min, 1);

    const step = width / (this.heartRateHistory.length - 1);

    return this.heartRateHistory.map((val, i) => {
      const x = i * step;
      const y = height - ((val - min) / range) * (height - 10) - 5;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }
}
