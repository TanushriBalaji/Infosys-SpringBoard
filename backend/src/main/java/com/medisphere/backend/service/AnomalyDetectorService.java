package com.medisphere.backend.service;

import com.medisphere.backend.model.Alert;
import com.medisphere.backend.model.VitalTelemetry;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class AnomalyDetectorService {

    // Store recent history per patient for rolling statistics
    private final Map<String, List<Double>> heartRateHistory = new ConcurrentHashMap<>();

    public Optional<Alert> detectAnomaly(VitalTelemetry telemetry) {
        if (telemetry == null || telemetry.getHeartRate() <= 0) {
            return Optional.empty();
        }

        String patientId = telemetry.getPatientId();
        List<Double> history = heartRateHistory.computeIfAbsent(patientId, k -> Collections.synchronizedList(new ArrayList<>()));

        history.add(telemetry.getHeartRate());

        // Keep last 10 readings
        if (history.size() > 10) {
            history.remove(0);
        }

        // Need at least 5 readings to compute baseline
        if (history.size() >= 5) {
            double mean = history.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            double stdDev = Math.sqrt(history.stream().mapToDouble(val -> Math.pow(val - mean, 2)).average().orElse(0.0));

            // If stdDev is significant and current value is > 2.5 stdDevs above mean
            if (stdDev > 2.0 && (telemetry.getHeartRate() - mean) > 2.5 * stdDev) {
                return Optional.of(new Alert(
                    patientId,
                    "STATISTICAL_ANOMALY",
                    "MODERATE",
                    "Heart Rate Spike",
                    telemetry.getHeartRate(),
                    "Baseline Mean: " + String.format("%.1f", mean) + " bpm",
                    "Unusual heart rate spike detected for patient " + patientId + ": " + telemetry.getHeartRate() + " bpm (Baseline mean: " + String.format("%.1f", mean) + " bpm)."
                ));
            }
        }

        return Optional.empty();
    }
}
