package com.medisphere.backend.repository;

import com.medisphere.backend.model.Alert;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AlertRepository extends MongoRepository<Alert, String> {
    List<Alert> findByPatientId(String patientId);
    List<Alert> findByStatusOrderByTimestampDesc(String status);
    List<Alert> findAllByOrderByTimestampDesc();
}
