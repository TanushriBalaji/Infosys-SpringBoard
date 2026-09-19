package com.medisphere.backend.repository;

import com.medisphere.backend.model.PatientData;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface PatientDataRepository
        extends MongoRepository<PatientData, String> {
}