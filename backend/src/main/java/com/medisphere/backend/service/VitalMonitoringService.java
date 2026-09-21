package com.medisphere.backend.service;

import com.medisphere.backend.model.Alert;
import com.medisphere.backend.model.RealtimeVital;
import com.medisphere.backend.model.VitalTelemetry;
import com.medisphere.backend.repository.AlertRepository;
import com.medisphere.backend.repository.PatientDataRepository;
import com.medisphere.backend.repository.RealtimeVitalRepository;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class VitalMonitoringService {

    private final AlertRepository alertRepository;
    private final RealtimeVitalRepository realtimeVitalRepository;
    private final PatientDataRepository patientDataRepository;
    private final ClinicalRuleEngine ruleEngine;
    private final AnomalyDetectorService anomalyDetector;

    private final List<SseEmitter> alertEmitters = new CopyOnWriteArrayList<>();
    private final Map<String, VitalTelemetry> latestTelemetry = new ConcurrentHashMap<>();

    public VitalMonitoringService(AlertRepository alertRepository,
                                  RealtimeVitalRepository realtimeVitalRepository,
                                  PatientDataRepository patientDataRepository,
                                  ClinicalRuleEngine ruleEngine,
                                  AnomalyDetectorService anomalyDetector) {
        this.alertRepository = alertRepository;
        this.realtimeVitalRepository = realtimeVitalRepository;
        this.patientDataRepository = patientDataRepository;
        this.ruleEngine = ruleEngine;
        this.anomalyDetector = anomalyDetector;
    }

    public void processTelemetry(VitalTelemetry telemetry) {
        // 1. Validate payload
        if (telemetry == null || telemetry.getPatientId() == null || telemetry.getPatientId().trim().isEmpty()) {
            System.err.println("Rejected invalid telemetry: empty payload or patientId");
            return;
        }

        String patientId = telemetry.getPatientId().trim();

        // 2. Confirm patientId corresponds to an existing patient in MongoDB
        boolean patientExists = patientDataRepository.existsById(patientId);
        if (!patientExists) {
            System.err.println("Warning: Telemetry received for unregistered patientId: " + patientId);
            // Allow processing if no patient was loaded yet or proceed with warning
        }

        // 3. Save the telemetry to MongoDB collection realtime_vitals
        try {
            RealtimeVital vitalDoc = new RealtimeVital(
                    patientId,
                    telemetry.getTimestamp(),
                    telemetry.getHeartRate(),
                    telemetry.getSpo2(),
                    telemetry.getSystolicBP(),
                    telemetry.getDiastolicBP(),
                    telemetry.getTemperature()
            );
            realtimeVitalRepository.save(vitalDoc);
        } catch (Exception e) {
            System.err.println("Failed to persist realtime vital document: " + e.getMessage());
        }

        // 4. Update current real-time vital state for that patient
        latestTelemetry.put(patientId, telemetry);

        // 5. Run the Clinical Rule Engine
        List<Alert> triggeredAlerts = ruleEngine.evaluateRules(telemetry);

        // 6. Run the statistical Anomaly Detector
        anomalyDetector.detectAnomaly(telemetry).ifPresent(triggeredAlerts::add);

        // 7. If an alert is generated, save it to the existing alerts collection
        for (Alert alert : triggeredAlerts) {
            try {
                Alert savedAlert = alertRepository.save(alert);
                // 8. Stream the alert through the existing SSE endpoint
                broadcastAlert(savedAlert);
            } catch (Exception e) {
                System.err.println("Failed to save/broadcast alert: " + e.getMessage());
            }
        }

        // 9. Stream latest vital information to Angular
        broadcastTelemetry(telemetry);
    }

    public SseEmitter subscribeSse() {
        SseEmitter emitter = new SseEmitter(0L); // Infinite timeout
        alertEmitters.add(emitter);

        emitter.onCompletion(() -> alertEmitters.remove(emitter));
        emitter.onTimeout(() -> alertEmitters.remove(emitter));
        emitter.onError((ex) -> alertEmitters.remove(emitter));

        // Send initial connection event
        try {
            emitter.send(SseEmitter.event().name("INIT").data("Connected to MediSphere Real-Time Alerts Stream"));
        } catch (IOException e) {
            alertEmitters.remove(emitter);
        }

        return emitter;
    }

    private void broadcastAlert(Alert alert) {
        List<SseEmitter> deadEmitters = new ArrayList<>();
        for (SseEmitter emitter : alertEmitters) {
            try {
                emitter.send(SseEmitter.event().name("ALERT").data(alert));
            } catch (IOException e) {
                deadEmitters.add(emitter);
            }
        }
        alertEmitters.removeAll(deadEmitters);
    }

    private void broadcastTelemetry(VitalTelemetry telemetry) {
        List<SseEmitter> deadEmitters = new ArrayList<>();
        for (SseEmitter emitter : alertEmitters) {
            try {
                emitter.send(SseEmitter.event().name("TELEMETRY").data(telemetry));
            } catch (IOException e) {
                deadEmitters.add(emitter);
            }
        }
        alertEmitters.removeAll(deadEmitters);
    }

    public Map<String, VitalTelemetry> getLatestTelemetry() {
        return latestTelemetry;
    }
}
