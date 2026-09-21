package com.medisphere.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medisphere.backend.model.VitalTelemetry;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class KafkaConsumerService {

    private final VitalMonitoringService monitoringService;
    private final ObjectMapper objectMapper;

    public KafkaConsumerService(VitalMonitoringService monitoringService) {
        this.monitoringService = monitoringService;
        this.objectMapper = new ObjectMapper();
    }

    @KafkaListener(
        topics = KafkaProducerService.TOPIC_PATIENT_VITALS,
        groupId = "medisphere-monitoring",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumeTelemetry(String message) {
        try {
            System.out.println("Kafka Consumer received telemetry message: " + message);
            VitalTelemetry telemetry = objectMapper.readValue(message, VitalTelemetry.class);
            monitoringService.processTelemetry(telemetry);
        } catch (Exception e) {
            System.err.println("Error parsing consumed Kafka message: " + e.getMessage());
        }
    }
}
