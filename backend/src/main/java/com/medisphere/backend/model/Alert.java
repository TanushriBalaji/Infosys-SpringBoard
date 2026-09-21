package com.medisphere.backend.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Document(collection = "alerts")
public class Alert {

    @Id
    private String alertId;

    private String patientId;
    private String alertType;
    private String severity;
    private String vitalName;
    private double vitalValue;
    private String threshold;
    private String message;
    private LocalDateTime timestamp;
    private String status; // ACTIVE, ACKNOWLEDGED, RESOLVED

    public Alert() {
        this.status = "ACTIVE";
        this.timestamp = LocalDateTime.now();
    }

    public Alert(String patientId, String alertType, String severity, String vitalName, double vitalValue, String threshold, String message) {
        this.patientId = patientId;
        this.alertType = alertType;
        this.severity = severity;
        this.vitalName = vitalName;
        this.vitalValue = vitalValue;
        this.threshold = threshold;
        this.message = message;
        this.status = "ACTIVE";
        this.timestamp = LocalDateTime.now();
    }

    public String getAlertId() {
        return alertId;
    }

    public void setAlertId(String alertId) {
        this.alertId = alertId;
    }

    public String getPatientId() {
        return patientId;
    }

    public void setPatientId(String patientId) {
        this.patientId = patientId;
    }

    public String getAlertType() {
        return alertType;
    }

    public void setAlertType(String alertType) {
        this.alertType = alertType;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public String getVitalName() {
        return vitalName;
    }

    public void setVitalName(String vitalName) {
        this.vitalName = vitalName;
    }

    public double getVitalValue() {
        return vitalValue;
    }

    public void setVitalValue(double vitalValue) {
        this.vitalValue = vitalValue;
    }

    public String getThreshold() {
        return threshold;
    }

    public void setThreshold(String threshold) {
        this.threshold = threshold;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
