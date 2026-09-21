package com.medisphere.backend.service;

import com.medisphere.backend.model.Alert;
import com.medisphere.backend.model.VitalTelemetry;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class ClinicalRuleEngine {

    public List<Alert> evaluateRules(VitalTelemetry telemetry) {
        List<Alert> alerts = new ArrayList<>();

        if (telemetry == null) {
            return alerts;
        }

        // Rule 1: Heart Rate >= 140 -> HIGH_HEART_RATE / CRITICAL
        if (telemetry.getHeartRate() >= 140) {
            alerts.add(new Alert(
                telemetry.getPatientId(),
                "HIGH_HEART_RATE",
                "CRITICAL",
                "Heart Rate",
                telemetry.getHeartRate(),
                ">= 140 bpm",
                "Critical tachycardia detected: Heart rate is " + telemetry.getHeartRate() + " bpm."
            ));
        }

        // Rule 2: SpO2 < 90 -> LOW_SPO2 / CRITICAL
        if (telemetry.getSpo2() > 0 && telemetry.getSpo2() < 90) {
            alerts.add(new Alert(
                telemetry.getPatientId(),
                "LOW_SPO2",
                "CRITICAL",
                "SpO2",
                telemetry.getSpo2(),
                "< 90%",
                "Severe hypoxemia detected: SpO2 level is " + telemetry.getSpo2() + "%."
            ));
        }

        // Rule 3: Systolic BP >= 180 -> HIGH_BLOOD_PRESSURE / CRITICAL
        if (telemetry.getSystolicBP() >= 180) {
            alerts.add(new Alert(
                telemetry.getPatientId(),
                "HIGH_BLOOD_PRESSURE",
                "CRITICAL",
                "Systolic Blood Pressure",
                telemetry.getSystolicBP(),
                ">= 180 mmHg",
                "Hypertensive crisis detected: Systolic BP is " + telemetry.getSystolicBP() + " mmHg."
            ));
        }

        // Rule 4: Temperature >= 39.0 -> HIGH_TEMPERATURE / HIGH
        if (telemetry.getTemperature() >= 39.0) {
            alerts.add(new Alert(
                telemetry.getPatientId(),
                "HIGH_TEMPERATURE",
                "HIGH",
                "Temperature",
                telemetry.getTemperature(),
                ">= 39.0 °C",
                "High fever detected: Core temperature is " + telemetry.getTemperature() + " °C."
            ));
        }

        return alerts;
    }
}
