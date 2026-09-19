package com.medisphere.backend.controller;

import com.medisphere.backend.model.PatientData;
import com.medisphere.backend.repository.PatientDataRepository;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/patients")
@CrossOrigin(origins = "http://localhost:4200")
public class PatientDataController {

    private final PatientDataRepository repository;

    public PatientDataController(PatientDataRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public List<PatientData> getAllPatients() {
        return repository.findAll();
    }

    @GetMapping("/count")
    public long getPatientCount() {
        return repository.count();
    }
}