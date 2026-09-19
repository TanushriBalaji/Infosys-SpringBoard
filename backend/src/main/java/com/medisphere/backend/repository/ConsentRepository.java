package com.medisphere.backend.repository;

import com.medisphere.backend.model.Consent;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface ConsentRepository extends MongoRepository<Consent, String> {

    Optional<Consent> findTopByPatientIdOrderByConsentDateDesc(String patientId);
}