package com.medisphere.backend.controller;

import com.medisphere.backend.model.Alert;
import com.medisphere.backend.model.VitalTelemetry;
import com.medisphere.backend.repository.AlertRepository;
import com.medisphere.backend.service.VitalMonitoringService;
import com.medisphere.backend.service.WearableSimulatorService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = {"http://localhost:4200", "http://127.0.0.1:4200"})
public class AlertController {

    private final AlertRepository alertRepository;
    private final VitalMonitoringService monitoringService;
    private final WearableSimulatorService simulatorService;

    public AlertController(AlertRepository alertRepository,
                           VitalMonitoringService monitoringService,
                           WearableSimulatorService simulatorService) {
        this.alertRepository = alertRepository;
        this.monitoringService = monitoringService;
        this.simulatorService = simulatorService;
    }

    @GetMapping("/alerts")
    public List<Alert> getAllAlerts() {
        return alertRepository.findAllByOrderByTimestampDesc();
    }

    @GetMapping("/alerts/{id}")
    public ResponseEntity<Alert> getAlertById(@PathVariable String id) {
        return alertRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/alerts/{id}/acknowledge")
    public ResponseEntity<Alert> acknowledgeAlert(@PathVariable String id) {
        return alertRepository.findById(id).map(alert -> {
            alert.setStatus("ACKNOWLEDGED");
            Alert saved = alertRepository.save(alert);
            return ResponseEntity.ok(saved);
        }).orElse(ResponseEntity.notFound().build());
    }

    @PutMapping("/alerts/{id}/resolve")
    public ResponseEntity<Alert> resolveAlert(@PathVariable String id) {
        return alertRepository.findById(id).map(alert -> {
            alert.setStatus("RESOLVED");
            Alert saved = alertRepository.save(alert);
            return ResponseEntity.ok(saved);
        }).orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/alerts/stream")
    public SseEmitter streamAlerts() {
        return monitoringService.subscribeSse();
    }

    @PostMapping("/simulator/start")
    public ResponseEntity<String> startSimulator() {
        simulatorService.setRunning(true);
        return ResponseEntity.ok("Wearable simulator started");
    }

    @PostMapping("/simulator/stop")
    public ResponseEntity<String> stopSimulator() {
        simulatorService.setRunning(false);
        return ResponseEntity.ok("Wearable simulator stopped");
    }

    @PostMapping("/simulator/select-patient")
    public ResponseEntity<Map<String, String>> selectSimulatorPatient(@RequestParam String patientId) {
        simulatorService.setActivePatientId(patientId);
        return ResponseEntity.ok(Map.of(
                "status", "SUCCESS",
                "activePatientId", simulatorService.getActivePatientId()
        ));
    }

    @GetMapping("/simulator/active-patient")
    public ResponseEntity<Map<String, String>> getActiveSimulatorPatient() {
        return ResponseEntity.ok(Map.of(
                "activePatientId", simulatorService.getActivePatientId()
        ));
    }

    @PostMapping("/simulator/trigger-abnormal")
    public ResponseEntity<VitalTelemetry> triggerAbnormal(
            @RequestParam(required = false) String patientId,
            @RequestParam(required = false, defaultValue = "HIGH_HEART_RATE") String condition) {
        VitalTelemetry telemetry = simulatorService.triggerAbnormalTelemetry(patientId, condition);
        return ResponseEntity.ok(telemetry);
    }
}
