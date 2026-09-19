package com.medisphere.backend.controller;

import com.medisphere.backend.model.Consent;
import com.medisphere.backend.repository.ConsentRepository;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Optional;

@RestController
@RequestMapping("/api/consent")
@CrossOrigin(origins = "http://localhost:4200")
public class ConsentController {

    private final ConsentRepository repository;

    public ConsentController(ConsentRepository repository) {
        this.repository = repository;
    }

    @PostMapping
    public Consent saveConsent(@RequestBody Consent consent) {

        consent.setConsentDate(LocalDateTime.now());

        return repository.save(consent);
    }

    @GetMapping("/{patientId}")
    public Optional<Consent> getLatestConsent(
            @PathVariable String patientId) {

        return repository
                .findTopByPatientIdOrderByConsentDateDesc(patientId);
    }
}