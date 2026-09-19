package com.medisphere.backend.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.List;
import java.util.Map;

@Document(collection = "patient_data")
public class PatientData {

    @Id
    private String id;

    private Map<String, Object> patient;
    private List<Map<String, Object>> observations;
    private List<Map<String, Object>> conditions;
    private List<Map<String, Object>> medications;
    private List<Map<String, Object>> encounters;
    private List<Map<String, Object>> diagnosticReports;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Map<String, Object> getPatient() {
        return patient;
    }

    public void setPatient(Map<String, Object> patient) {
        this.patient = patient;
    }

    public List<Map<String, Object>> getObservations() {
        return observations;
    }

    public void setObservations(List<Map<String, Object>> observations) {
        this.observations = observations;
    }

    public List<Map<String, Object>> getConditions() {
        return conditions;
    }

    public void setConditions(List<Map<String, Object>> conditions) {
        this.conditions = conditions;
    }

    public List<Map<String, Object>> getMedications() {
        return medications;
    }

    public void setMedications(List<Map<String, Object>> medications) {
        this.medications = medications;
    }

    public List<Map<String, Object>> getEncounters() {
        return encounters;
    }

    public void setEncounters(List<Map<String, Object>> encounters) {
        this.encounters = encounters;
    }

    public List<Map<String, Object>> getDiagnosticReports() {
        return diagnosticReports;
    }

    public void setDiagnosticReports(List<Map<String, Object>> diagnosticReports) {
        this.diagnosticReports = diagnosticReports;
    }
}