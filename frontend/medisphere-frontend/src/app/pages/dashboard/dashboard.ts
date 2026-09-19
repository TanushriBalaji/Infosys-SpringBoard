import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import {
  FederatedAiService,
  FederatedStatus,
  FederatedResults,
  HospitalResult
} from '../../services/federated-ai.service';

interface PatientCard {
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
  // FEDERATED AI
  // =========================================================

  federatedStatus: FederatedStatus | null = null;

  federatedResults: FederatedResults | null = null;

  hospitalResults: HospitalResult[] = [];

  aiMessage = '';

  aiError = '';


  // =========================================================
  // CONSTRUCTOR
  // =========================================================

  constructor(
    private http: HttpClient,
    private federatedAiService: FederatedAiService
  ) {}


  // =========================================================
  // INITIALIZATION
  // =========================================================

  ngOnInit(): void {

    this.loadPatients();
    this.loadFederatedAI();
  }


  // =========================================================
  // FEDERATED AI
  // =========================================================

  loadFederatedAI(): void {
    this.aiError = '';
    this.aiMessage = '';
    this.loadFederatedStatus();
    this.loadFederatedResults();
    this.loadFederatedHospitals();
  }

  loadFederatedStatus(): void {
    this.federatedAiService.getStatus().subscribe({
      next: (data) => { this.federatedStatus = data; console.log('Federated AI status:', data); },
      error: (error) => { console.error('Federated AI service unavailable:', error); this.aiError = 'Federated AI service is not running on port 5001.'; }
    });
  }

  loadFederatedResults(): void {
    this.federatedAiService.getResults().subscribe({
      next: (data) => {
        this.federatedResults = data;
        this.hospitalResults = data.hospitals;
        this.aiMessage = 'Federated Random Forest results loaded successfully.';
        console.log('Federated AI results:', data);
      },
      error: (error) => console.error('Could not load federated results:', error)
    });
  }

  loadFederatedHospitals(): void {
    this.federatedAiService.getHospitals().subscribe({
      next: (data) => {
        this.hospitalResults = data.hospitals;
        console.log('Federated hospitals:', data);
      },
      error: (error) => console.error('Could not load hospital information:', error)
    });
  }

  // =========================================================
  // PATIENT DATA
  // =========================================================

  loadPatients(): void {

    this.loading = true;
    this.error = '';

    this.http
      .get<any[]>('http://localhost:8080/api/patients')
      .subscribe({

        next: (data) => {

          console.log(
            'MongoDB patient data:',
            data
          );

          this.patients =
            data.map(
              (item, index) =>
                this.convertPatient(
                  item,
                  index
                )
            );

          this.loading = false;

          this.currentPage = 1;
        },

        error: (err) => {

          console.error(
            'Patient API error:',
            err
          );

          this.error =
            'Unable to connect to the MediSphere backend.';

          this.loading = false;
        }

      });

  }


  convertPatient(
    item: any,
    index: number
  ): PatientCard {

    const patient =
      item.patient || {};

    const resource =
      patient.resource || patient;

    const id =
      resource.id ||
      item.id ||
      `Patient-${index + 1}`;

    return {

      id: id,

      name:
        this.getPatientName(resource),

      gender:
        resource.gender || 'Unknown',

      birthDate:
        resource.birthDate || 'Unknown',

      heartRate:
        this.findObservation(
          item.observations || [],
          [
            'heart rate',
            'heart_rate',
            'heartrate'
          ],
          'bpm'
        ),

      bloodPressure:
        this.findBloodPressure(
          item.observations || []
        ),

      glucose:
        this.findObservation(
          item.observations || [],
          [
            'glucose',
            'blood glucose',
            'blood sugar'
          ],
          'mg/dL'
        ),

      bmi:
        this.findObservation(
          item.observations || [],
          [
            'bmi',
            'body mass index'
          ],
          'kg/m2'
        ),

      conditions:
        this.getConditions(
          item.conditions || []
        ),

      medications:
        this.getMedications(
          item.medications || []
        )
    };
  }


  getPatientName(
    patient: any
  ): string {

    if (
      Array.isArray(patient.name) &&
      patient.name.length > 0
    ) {

      const name =
        patient.name[0];

      const given =
        Array.isArray(name.given)
          ? name.given.join(' ')
          : (name.given || '');

      const family =
        name.family || '';

      const fullName =
        `${given} ${family}`.trim();

      if (fullName) {
        return fullName;
      }
    }

    if (
      typeof patient.name === 'string'
    ) {

      return patient.name;
    }

    return 'Unknown Patient';
  }


  findObservation(
    observations: any[],
    keywords: string[],
    defaultUnit: string
  ): string {

    for (
      const observation of observations
    ) {

      const resource =
        observation.resource ||
        observation;

      const text =
        JSON.stringify(resource)
          .toLowerCase();

      const matched =
        keywords.some(
          keyword =>
            text.includes(
              keyword.toLowerCase()
            )
        );

      if (!matched) {
        continue;
      }

      const value =
        this.extractObservationValue(
          resource
        );

      if (value !== null) {

        const unit =
          this.extractObservationUnit(
            resource
          ) || defaultUnit;

        return `${value} ${unit}`;
      }
    }

    return '--';
  }


  findBloodPressure(
    observations: any[]
  ): string {

    let systolic: any = null;

    let diastolic: any = null;

    for (
      const observation of observations
    ) {

      const resource =
        observation.resource ||
        observation;

      const text =
        JSON.stringify(resource)
          .toLowerCase();

      if (
        !text.includes(
          'blood pressure'
        ) &&
        !text.includes('85354-9')
      ) {
        continue;
      }

      if (!resource.component) {
        continue;
      }

      for (
        const component of resource.component
      ) {

        const componentText =
          JSON.stringify(component)
            .toLowerCase();

        const value =
          this.extractObservationValue(
            component
          );

        if (value === null) {
          continue;
        }

        if (
          componentText.includes(
            'systolic'
          ) ||
          componentText.includes(
            '8480-6'
          )
        ) {
          systolic = value;
        }

        if (
          componentText.includes(
            'diastolic'
          ) ||
          componentText.includes(
            '8462-4'
          )
        ) {
          diastolic = value;
        }
      }
    }

    if (
      systolic !== null &&
      diastolic !== null
    ) {

      return `${systolic}/${diastolic} mmHg`;
    }

    return '--/-- mmHg';
  }


  extractObservationValue(
    resource: any
  ): any {

    if (resource.valueQuantity) {
      return resource.valueQuantity.value;
    }

    if (
      resource.valueInteger !== undefined
    ) {
      return resource.valueInteger;
    }

    if (
      resource.valueDecimal !== undefined
    ) {
      return resource.valueDecimal;
    }

    if (
      resource.valueString !== undefined
    ) {
      return resource.valueString;
    }

    if (
      resource.valueCodeableConcept
    ) {

      return (
        resource.valueCodeableConcept.text ||
        resource.valueCodeableConcept
          .coding?.[0]?.display ||
        null
      );
    }

    return null;
  }


  extractObservationUnit(
    resource: any
  ): string {

    if (resource.valueQuantity) {

      return (
        resource.valueQuantity.unit ||
        resource.valueQuantity.code ||
        ''
      );
    }

    return '';
  }


  getConditions(
    conditions: any[]
  ): string[] {

    const result: string[] = [];

    for (
      const condition of conditions
    ) {

      const resource =
        condition.resource ||
        condition;

      const text =
        resource.code?.text ||
        resource.code?.coding?.[0]?.display ||
        condition.text ||
        condition.display;

      if (text) {
        result.push(text);
      }
    }

    return [
      ...new Set(result)
    ].slice(0, 4);
  }


  getMedications(
    medications: any[]
  ): string[] {

    const result: string[] = [];

    for (
      const medication of medications
    ) {

      const resource =
        medication.resource ||
        medication;

      const text =
        resource.medicationCodeableConcept?.text ||
        resource.medicationCodeableConcept
          ?.coding?.[0]?.display ||
        resource.medicationReference?.display ||
        resource.medication?.display ||
        medication.text ||
        medication.display;

      if (text) {
        result.push(text);
      }
    }

    return [
      ...new Set(result)
    ].slice(0, 4);
  }


  // =========================================================
  // SEARCH
  // =========================================================

  get filteredPatients(): PatientCard[] {

    const term =
      this.searchTerm
        .trim()
        .toLowerCase();

    if (!term) {
      return this.patients;
    }

    return this.patients.filter(
      patient =>
        patient.name
          .toLowerCase()
          .includes(term) ||

        patient.id
          .toLowerCase()
          .includes(term) ||

        patient.gender
          .toLowerCase()
          .includes(term)
    );
  }


  // =========================================================
  // PAGINATION
  // =========================================================

  get totalPages(): number {

    return Math.max(
      1,
      Math.ceil(
        this.filteredPatients.length /
        this.pageSize
      )
    );
  }


  get displayedPatients(): PatientCard[] {

    const start =
      (this.currentPage - 1) *
      this.pageSize;

    return this.filteredPatients.slice(
      start,
      start + this.pageSize
    );
  }


  nextPage(): void {

    if (
      this.currentPage <
      this.totalPages
    ) {

      this.currentPage++;

      window.scrollTo(0, 0);
    }
  }


  previousPage(): void {

    if (
      this.currentPage > 1
    ) {

      this.currentPage--;

      window.scrollTo(0, 0);
    }
  }


  // =========================================================
  // TABS
  // =========================================================

  setTab(
    tab: string
  ): void {

    this.activeTab = tab;

    window.scrollTo(
      0,
      0
    );
  }


  // =========================================================
  // DIGITAL TWIN
  // =========================================================

  openPatient(
    patient: PatientCard
  ): void {

    this.selectedPatient =
      patient;

    this.activeTab =
      'digital-twin';

    this.consentMessage = '';

    this.consentError = '';

    this.loadPatientConsent();
  }


  closePatient(): void {

    this.selectedPatient =
      null;

    this.consentMessage = '';

    this.consentError = '';
  }


  openPatientById(
    id: string
  ): void {

    const patient =
      this.patients.find(
        item =>
          item.id === id
      );

    if (patient) {

      this.openPatient(
        patient
      );
    }
  }


  // =========================================================
  // CONSENT
  // =========================================================

  toggleConsent(): void {

    this.consentGranted =
      !this.consentGranted;

    if (
      !this.consentGranted
    ) {

      this.selectedScopes = [];
    }
  }


  toggleScope(
    scope: string
  ): void {

    if (!this.consentGranted) {
      return;
    }

    const index =
      this.selectedScopes.indexOf(
        scope
      );

    if (index >= 0) {

      this.selectedScopes.splice(
        index,
        1
      );

    } else {

      this.selectedScopes.push(
        scope
      );
    }
  }


  saveConsent(): void {

    this.consentError = '';

    this.consentMessage = '';

    if (!this.selectedPatient) {

      this.consentError =
        'Please select a patient first.';

      return;
    }

    if (!this.consentGranted) {

      this.consentError =
        'Please grant consent before saving.';

      return;
    }

    if (
      this.selectedScopes.length === 0
    ) {

      this.consentError =
        'Please select at least one data scope.';

      return;
    }

    this.consentLoading = true;

    const consent: ConsentRecord = {

      patientId:
        this.selectedPatient.id,

      purpose:
        this.consentPurpose,

      duration:
        this.accessDuration,

      requestedBy:
        this.requestedBy,

      scopes:
        [...this.selectedScopes],

      granted: true,

      date:
        new Date().toISOString()
    };

    this.consents.push(
      consent
    );

    console.log(
      'Patient consent:',
      consent
    );

    this.consentLoading = false;

    this.consentMessage =
      'Consent saved successfully. Data access has been granted according to the selected permissions.';
  }


  revokeConsent(): void {

    if (!this.selectedPatient) {
      return;
    }

    this.consents =
      this.consents.filter(
        consent =>
          consent.patientId !==
          this.selectedPatient!.id
      );

    this.consentGranted = false;

    this.selectedScopes = [];

    this.consentMessage =
      'Consent revoked. Data access has been removed.';
  }


  loadPatientConsent(): void {

    if (!this.selectedPatient) {
      return;
    }

    const existing =
      this.consents.find(
        consent =>
          consent.patientId ===
          this.selectedPatient!.id
      );

    if (existing) {

      this.consentGranted =
        existing.granted;

      this.consentPurpose =
        existing.purpose;

      this.accessDuration =
        existing.duration;

      this.requestedBy =
        existing.requestedBy;

      this.selectedScopes =
        [...existing.scopes];

    } else {

      this.consentGranted = false;

      this.selectedScopes = [
        'Basic Demographics',
        'Vital Signs'
      ];
    }
  }


  hasConsent(): boolean {

    if (!this.selectedPatient) {
      return false;
    }

    return this.consents.some(
      consent =>
        consent.patientId ===
        this.selectedPatient!.id &&
        consent.granted
    );
  }

}