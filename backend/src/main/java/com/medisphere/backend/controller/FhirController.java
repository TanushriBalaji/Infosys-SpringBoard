package com.medisphere.backend.controller;

import com.medisphere.backend.service.FhirService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/fhir")
public class FhirController {

    private final FhirService fhirService;

    public FhirController(FhirService fhirService) {
        this.fhirService = fhirService;
    }

    @GetMapping("/patients")
    public String getPatients() {
        return fhirService.getPatients();
    }
}