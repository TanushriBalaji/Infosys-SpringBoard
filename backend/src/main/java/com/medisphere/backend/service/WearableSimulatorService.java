package com.medisphere.backend.service;

import com.medisphere.backend.model.PatientData;
import com.medisphere.backend.model.VitalTelemetry;
import com.medisphere.backend.repository.PatientDataRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Random;
import java.util.concurrent.atomic.AtomicBoolean;

@Service
public class WearableSimulatorService {

    private final KafkaProducerService producerService;
    private final PatientDataRepository patientDataRepository;

    private final Random random = new Random();
    private final AtomicBoolean running = new AtomicBoolean(true);

    private volatile String activePatientId = null;

    public WearableSimulatorService(KafkaProducerService producerService, PatientDataRepository patientDataRepository) {
        this.producerService = producerService;
        this.patientDataRepository = patientDataRepository;
    }

    @PostConstruct
    public void init() {
        refreshActivePatientId();
    }

    public synchronized String refreshActivePatientId() {
        if (activePatientId == null || activePatientId.isEmpty()) {
            List<PatientData> firstPatients = patientDataRepository.findAll();
            if (!firstPatients.isEmpty()) {
                activePatientId = firstPatients.get(0).getId();
                System.out.println("Wearable Simulator bound to real MongoDB patient ID: " + activePatientId);
            } else {
                activePatientId = "urn:uuid:5cbc121b-cd71-4428-b8b7-31e53eba8184";
            }
        }
        return activePatientId;
    }

    public void setActivePatientId(String patientId) {
        if (patientId != null && !patientId.trim().isEmpty()) {
            this.activePatientId = patientId.trim();
            System.out.println("Wearable Simulator active patient switched to: " + this.activePatientId);
        }
    }

    public String getActivePatientId() {
        if (activePatientId == null) {
            refreshActivePatientId();
        }
        return activePatientId;
    }

    public void setRunning(boolean isRunning) {
        this.running.set(isRunning);
    }

    public boolean isRunning() {
        return this.running.get();
    }

    @Scheduled(fixedRate = 4000)
    public void generateNormalTelemetry() {
        if (!running.get()) {
            return;
        }

        String targetPatientId = getActivePatientId();

        // Normal mode generates realistic values in prototype ranges:
        // heartRate: 70–95
        // spo2: 95–100
        // systolicBP: 110–135
        // diastolicBP: 65–85
        // temperature: 36.5–37.5
        VitalTelemetry telemetry = new VitalTelemetry(
                targetPatientId,
                Instant.now().toString(),
                70 + random.nextInt(26),          // 70 - 95 bpm
                95 + random.nextInt(6),           // 95 - 100 % SpO2
                110 + random.nextInt(26),         // 110 - 135 mmHg Systolic
                65 + random.nextInt(21),          // 65 - 85 mmHg Diastolic
                Math.round((36.5 + (random.nextDouble() * 1.0)) * 10.0) / 10.0 // 36.5 - 37.5 °C
        );

        producerService.sendTelemetry(telemetry);
    }

    public VitalTelemetry triggerAbnormalTelemetry(String patientId, String condition) {
        String pid = (patientId != null && !patientId.trim().isEmpty()) ? patientId.trim() : getActivePatientId();
        VitalTelemetry telemetry;

        if ("LOW_SPO2".equalsIgnoreCase(condition)) {
            telemetry = new VitalTelemetry(pid, Instant.now().toString(), 85.0, 87.0, 122.0, 78.0, 37.0);
        } else if ("HIGH_BP".equalsIgnoreCase(condition)) {
            telemetry = new VitalTelemetry(pid, Instant.now().toString(), 96.0, 96.0, 185.0, 110.0, 37.2);
        } else if ("HIGH_TEMP".equalsIgnoreCase(condition)) {
            telemetry = new VitalTelemetry(pid, Instant.now().toString(), 108.0, 95.0, 130.0, 84.0, 39.4);
        } else {
            // Default demo event per prompt: heartRate = 145
            telemetry = new VitalTelemetry(pid, Instant.now().toString(), 145.0, 97.0, 135.0, 88.0, 37.2);
        }

        producerService.sendTelemetry(telemetry);
        return telemetry;
    }
}
