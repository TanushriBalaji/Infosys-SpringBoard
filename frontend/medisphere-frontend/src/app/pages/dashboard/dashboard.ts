import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PatientDataService } from '../../services/patient-data.service';
import { RiskPredictionService, RiskPrediction, AiHealth } from '../../services/risk-prediction.service';

export interface PatientCard {
  id: string;
  name: string;
  gender: string;
  birthDate: string;
  heartRate: string;
  bloodPressure: string;
  glucose: string;
  bmi: string;
  conditions: string[];
  medications: string[];
}

interface ConsentRecord {
  patientId: string;
  purpose: string;
  duration: string;
  requestedBy: string;
  scopes: string[];
  granted: boolean;
  date: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {

  patients: PatientCard[] = [];
  private rawPatientsMap: Map<string, any> = new Map();

  loading = true;
  error = '';

  searchTerm = '';

  currentPage = 1;
  pageSize = 12;

  activeTab = 'patients';

  selectedPatient: PatientCard | null = null;

  consentGranted = false;
  consentPurpose = 'Clinical Care';
  accessDuration = '24 Hours';
  requestedBy = 'Doctor';

  selectedScopes: string[] = [
    'Basic Demographics',
    'Vital Signs'
  ];

  consentError = '';
  consentLoading = false;
  consentMessage = '';

  private consents: ConsentRecord[] = [];

  // =========================================================
  // AI PREDICTION
  // =========================================================
  aiHealth: AiHealth | null = null;
  aiPrediction: RiskPrediction | null = null;
  predictionLoading = false;
  predictionMessage = '';
  predictionError = '';

  constructor(
    private patientDataService: PatientDataService,
    private riskPredictionService: RiskPredictionService
  ) {}

  ngOnInit(): void {
    this.loadPatients();
    this.checkAiHealth();
  }

  // =========================================================
  // AI HEALTH & PREDICTION
  // =========================================================
  checkAiHealth(): void {
    this.riskPredictionService.getHealth().subscribe({
      next: (health) => {
        this.aiHealth = health;
        console.log('AI Service Health:', health);
      },
      error: (err) => {
        console.warn('AI Service health check failed:', err);
        this.aiHealth = {
          status: 'DOWN',
          cvd_model_loaded: false,
          diabetes_model_loaded: false,
          error: 'AI service unreachable at http://127.0.0.1:8000'
        };
      }
    });
  }

  predictSelectedPatient(): void {
    if (!this.selectedPatient) {
      this.predictionError = 'No patient selected.';
      return;
    }

    this.predictionLoading = true;
    this.predictionError = '';
    this.predictionMessage = '';

    const rawItem = this.rawPatientsMap.get(this.selectedPatient.id);
    const payload = this.buildPatientPredictionPayload(this.selectedPatient, rawItem);

    console.log('Sending prediction payload to AI service:', payload);

    this.riskPredictionService.predict(payload).subscribe({
      next: (res: RiskPrediction) => {
        this.aiPrediction = res;
        this.predictionLoading = false;
        this.predictionMessage = `Risk prediction calculated for patient ${this.selectedPatient?.name}.`;
        console.log('AI Prediction result:', res);
      },
      error: (err) => {
        console.error('Prediction call error:', err);
        this.predictionLoading = false;
        this.predictionError = err.error?.detail || 'Failed to complete risk prediction with AI service.';
      }
    });
  }

  formatPercentage(val: number | undefined): string {
    if (val === undefined || val === null) return '--%';
    return `${val.toFixed(1)}%`;
  }

  getRiskClass(level: string | undefined): string {
    if (!level) return '';
    switch (level.toUpperCase()) {
      case 'HIGH':
        return 'risk-high';
      case 'MODERATE':
        return 'risk-moderate';
      case 'LOW':
        return 'risk-low';
      default:
        return '';
    }
  }

  private buildPatientPredictionPayload(card: PatientCard, rawItem: any): any {
    const rawPatient = rawItem?.patient?.resource || rawItem?.patient || {};
    const observations = rawItem?.observations || [];

    const birthDate = rawPatient.birthDate || card.birthDate;
    const age = this.calculateAge(birthDate);

    const genderStr = rawPatient.gender || card.gender;
    let genderVal = -1;
    if (genderStr && genderStr.toLowerCase() === 'male') {
      genderVal = 1;
    } else if (genderStr && genderStr.toLowerCase() === 'female') {
      genderVal = 0;
    }

    const getObservationValue = (code: string): number | null => {
      for (const obs of observations) {
        const resource = obs.resource || obs;
        const codings = resource.code?.coding || [];
        for (const c of codings) {
          if (c.code === code) {
            if (resource.valueQuantity?.value !== undefined) {
              return parseFloat(resource.valueQuantity.value);
            }
          }
        }
        if (resource.component && Array.isArray(resource.component)) {
          for (const comp of resource.component) {
            const compCodings = comp.code?.coding || [];
            for (const c of compCodings) {
              if (c.code === code) {
                if (comp.valueQuantity?.value !== undefined) {
                  return parseFloat(comp.valueQuantity.value);
                }
              }
            }
          }
        }
      }
      return null;
    };

    return {
      patient_id: card.id,
      age: age,
      gender: genderVal,
      height_cm: getObservationValue('8302-2'),
      weight_kg: getObservationValue('29463-7'),
      bmi: getObservationValue('39156-5'),
      systolic_bp: getObservationValue('8480-6'),
      diastolic_bp: getObservationValue('8462-4'),
      glucose: getObservationValue('2339-0'),
      hba1c: getObservationValue('4548-4'),
      hdl_cholesterol: getObservationValue('2085-9'),
      total_cholesterol: getObservationValue('2093-3'),
      triglycerides: getObservationValue('2571-8'),
      creatinine: getObservationValue('38483-4'),
      calcium: getObservationValue('49765-1'),
      sodium: getObservationValue('2947-0'),
      potassium: getObservationValue('6298-4')
    };
  }

  private calculateAge(birthDateStr: string): number {
    if (!birthDateStr || birthDateStr === 'Unknown') return 50;
    try {
      const birth = new Date(birthDateStr);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
        age--;
      }
      return age > 0 ? age : 50;
    } catch {
      return 50;
    }
  }

  // =========================================================
  // PATIENT DATA
  // =========================================================
  loadPatients(): void {
    this.loading = true;
    this.error = '';

    this.patientDataService.getPatients().subscribe({
      next: (data) => {
        console.log('MongoDB patient data received:', data);
        this.rawPatientsMap.clear();

        this.patients = data.map((item, index) => {
          const card = this.convertPatient(item, index);
          this.rawPatientsMap.set(card.id, item);
          return card;
        });

        this.loading = false;
        this.currentPage = 1;
      },
      error: (err) => {
        console.error('Patient API error:', err);
        this.error = 'Unable to connect to the MediSphere Spring Boot backend at http://localhost:8080/api/patients.';
        this.loading = false;
      }
    });
  }

  convertPatient(item: any, index: number): PatientCard {
    const patient = item.patient || {};
    const resource = patient.resource || patient;
    const id = resource.id || item.id || `Patient-${index + 1}`;

    return {
      id: id,
      name: this.getPatientName(resource),
      gender: resource.gender || 'Unknown',
      birthDate: resource.birthDate || 'Unknown',
      heartRate: this.findObservation(
        item.observations || [],
        ['heart rate', 'heart_rate', 'heartrate', '88371-0', '8837-1'],
        'bpm'
      ),
      bloodPressure: this.findBloodPressure(item.observations || []),
      glucose: this.findObservation(
        item.observations || [],
        ['glucose', 'blood glucose', 'blood sugar', '2339-0'],
        'mg/dL'
      ),
      bmi: this.findObservation(
        item.observations || [],
        ['bmi', 'body mass index', '39156-5'],
        'kg/m2'
      ),
      conditions: this.getConditions(item.conditions || []),
      medications: this.getMedications(item.medications || [])
    };
  }

  getPatientName(patient: any): string {
    if (Array.isArray(patient.name) && patient.name.length > 0) {
      const name = patient.name[0];
      const given = Array.isArray(name.given) ? name.given.join(' ') : (name.given || '');
      const family = name.family || '';
      const fullName = `${given} ${family}`.trim();
      if (fullName) {
        return fullName;
      }
    }
    if (typeof patient.name === 'string') {
      return patient.name;
    }
    return 'Unknown Patient';
  }

  findObservation(observations: any[], keywords: string[], defaultUnit: string): string {
    for (const observation of observations) {
      const resource = observation.resource || observation;
      const text = JSON.stringify(resource).toLowerCase();
      const matched = keywords.some(keyword => text.includes(keyword.toLowerCase()));
      if (!matched) {
        continue;
      }
      const value = this.extractObservationValue(resource);
      if (value !== null) {
        const unit = this.extractObservationUnit(resource) || defaultUnit;
        return `${value} ${unit}`;
      }
    }
    return '--';
  }

  findBloodPressure(observations: any[]): string {
    let systolic: any = null;
    let diastolic: any = null;

    for (const observation of observations) {
      const resource = observation.resource || observation;

      if (resource.component && Array.isArray(resource.component)) {
        for (const comp of resource.component) {
          const compText = JSON.stringify(comp).toLowerCase();
          const val = comp.valueQuantity?.value;
          if (val === undefined || val === null) continue;

          if (compText.includes('systolic') || compText.includes('8480-6')) {
            systolic = val;
          }
          if (compText.includes('diastolic') || compText.includes('8462-4')) {
            diastolic = val;
          }
        }
      }
    }

    if (systolic !== null && diastolic !== null) {
      return `${systolic}/${diastolic} mmHg`;
    }
    return '--/-- mmHg';
  }

  extractObservationValue(resource: any): any {
    if (resource.valueQuantity) {
      return resource.valueQuantity.value;
    }
    if (resource.valueInteger !== undefined) {
      return resource.valueInteger;
    }
    if (resource.valueDecimal !== undefined) {
      return resource.valueDecimal;
    }
    if (resource.valueString !== undefined) {
      return resource.valueString;
    }
    if (resource.valueCodeableConcept) {
      return resource.valueCodeableConcept.text || resource.valueCodeableConcept.coding?.[0]?.display || null;
    }
    return null;
  }

  extractObservationUnit(resource: any): string {
    if (resource.valueQuantity) {
      return resource.valueQuantity.unit || resource.valueQuantity.code || '';
    }
    return '';
  }

  getConditions(conditions: any[]): string[] {
    const result: string[] = [];
    for (const condition of conditions) {
      const resource = condition.resource || condition;
      const text = resource.code?.text || resource.code?.coding?.[0]?.display || condition.text || condition.display;
      if (text) {
        result.push(text);
      }
    }
    return [...new Set(result)].slice(0, 4);
  }

  getMedications(medications: any[]): string[] {
    const result: string[] = [];
    for (const medication of medications) {
      const resource = medication.resource || medication;
      const text = resource.medicationCodeableConcept?.text ||
        resource.medicationCodeableConcept?.coding?.[0]?.display ||
        resource.medicationReference?.display ||
        resource.medication?.display ||
        medication.text ||
        medication.display;
      if (text) {
        result.push(text);
      }
    }
    return [...new Set(result)].slice(0, 4);
  }

  // =========================================================
  // SEARCH & PAGINATION
  // =========================================================
  get filteredPatients(): PatientCard[] {
    const term = this.searchTerm.trim().toLowerCase();
    if (!term) {
      return this.patients;
    }
    return this.patients.filter(patient =>
      patient.name.toLowerCase().includes(term) ||
      patient.id.toLowerCase().includes(term) ||
      patient.gender.toLowerCase().includes(term)
    );
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filteredPatients.length / this.pageSize));
  }

  get displayedPatients(): PatientCard[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filteredPatients.slice(start, start + this.pageSize);
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      window.scrollTo(0, 0);
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      window.scrollTo(0, 0);
    }
  }

  // =========================================================
  // TABS & DIGITAL TWIN
  // =========================================================
  setTab(tab: string): void {
    this.activeTab = tab;
    window.scrollTo(0, 0);
  }

  openPatient(patient: PatientCard): void {
    this.selectedPatient = patient;
    this.activeTab = 'digital-twin';
    this.consentMessage = '';
    this.consentError = '';
    this.aiPrediction = null;
    this.predictionMessage = '';
    this.predictionError = '';
    this.loadPatientConsent();
  }

  closePatient(): void {
    this.selectedPatient = null;
    this.aiPrediction = null;
    this.consentMessage = '';
    this.consentError = '';
  }

  openPatientById(id: string): void {
    const patient = this.patients.find(item => item.id === id);
    if (patient) {
      this.openPatient(patient);
    }
  }

  // =========================================================
  // CONSENT
  // =========================================================
  toggleConsent(): void {
    this.consentGranted = !this.consentGranted;
    if (!this.consentGranted) {
      this.selectedScopes = [];
    }
  }

  toggleScope(scope: string): void {
    if (!this.consentGranted) {
      return;
    }
    const index = this.selectedScopes.indexOf(scope);
    if (index >= 0) {
      this.selectedScopes.splice(index, 1);
    } else {
      this.selectedScopes.push(scope);
    }
  }

  saveConsent(): void {
    this.consentError = '';
    this.consentMessage = '';
    if (!this.selectedPatient) {
      this.consentError = 'Please select a patient first.';
      return;
    }
    if (!this.consentGranted) {
      this.consentError = 'Please grant consent before saving.';
      return;
    }
    if (this.selectedScopes.length === 0) {
      this.consentError = 'Please select at least one data scope.';
      return;
    }

    this.consentLoading = true;
    const consent: ConsentRecord = {
      patientId: this.selectedPatient.id,
      purpose: this.consentPurpose,
      duration: this.accessDuration,
      requestedBy: this.requestedBy,
      scopes: [...this.selectedScopes],
      granted: true,
      date: new Date().toISOString()
    };

    this.consents.push(consent);
    console.log('Patient consent:', consent);
    this.consentLoading = false;
    this.consentMessage = 'Consent saved successfully. Data access has been granted according to the selected permissions.';
  }

  revokeConsent(): void {
    if (!this.selectedPatient) {
      return;
    }
    this.consents = this.consents.filter(consent => consent.patientId !== this.selectedPatient!.id);
    this.consentGranted = false;
    this.selectedScopes = [];
    this.consentMessage = 'Consent revoked. Data access has been removed.';
  }

  loadPatientConsent(): void {
    if (!this.selectedPatient) {
      return;
    }
    const existing = this.consents.find(consent => consent.patientId === this.selectedPatient!.id);
    if (existing) {
      this.consentGranted = existing.granted;
      this.consentPurpose = existing.purpose;
      this.accessDuration = existing.duration;
      this.requestedBy = existing.requestedBy;
      this.selectedScopes = [...existing.scopes];
    } else {
      this.consentGranted = false;
      this.selectedScopes = ['Basic Demographics', 'Vital Signs'];
    }
  }

  hasConsent(): boolean {
    if (!this.selectedPatient) {
      return false;
    }
    return this.consents.some(consent => consent.patientId === this.selectedPatient!.id && consent.granted);
  }
}
