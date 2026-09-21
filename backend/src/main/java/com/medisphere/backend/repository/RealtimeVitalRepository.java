package com.medisphere.backend.repository;

import com.medisphere.backend.model.RealtimeVital;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface RealtimeVitalRepository extends MongoRepository<RealtimeVital, String> {

    Optional<RealtimeVital> findFirstByPatientIdOrderByTimestampDesc(String patientId);

    List<RealtimeVital> findTop100ByPatientIdOrderByTimestampDesc(String patientId);

    List<RealtimeVital> findByPatientIdOrderByTimestampDesc(String patientId);
}
