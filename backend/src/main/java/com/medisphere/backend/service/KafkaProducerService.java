package com.medisphere.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.medisphere.backend.model.VitalTelemetry;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class KafkaProducerService {

    public static final String TOPIC_PATIENT_VITALS = "patient-vitals";

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    public KafkaProducerService(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = new ObjectMapper();
    }

    public void sendTelemetry(VitalTelemetry telemetry) {
        try {
            String jsonPayload = objectMapper.writeValueAsString(telemetry);
            kafkaTemplate.send(TOPIC_PATIENT_VITALS, telemetry.getPatientId(), jsonPayload);
            System.out.println("Kafka Producer sent telemetry for patient " + telemetry.getPatientId() + ": " + jsonPayload);
        } catch (Exception e) {
            System.err.println("Failed to send Kafka telemetry message: " + e.getMessage());
        }
    }
}
