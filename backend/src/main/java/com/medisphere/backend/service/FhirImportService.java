package com.medisphere.backend.service;

import ca.uhn.fhir.context.FhirContext;
import org.hl7.fhir.r4.model.Bundle;
import org.hl7.fhir.r4.model.Resource;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.medisphere.backend.model.PatientData;
import com.medisphere.backend.repository.PatientDataRepository;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class FhirImportService {

    private final PatientDataRepository repository;

    private final FhirContext fhirContext;

    private final ObjectMapper objectMapper;

    public FhirImportService(PatientDataRepository repository) {

        this.repository = repository;

        this.fhirContext = FhirContext.forR4();

        this.objectMapper = new ObjectMapper();
    }

    public int importAllPatients() throws IOException {

        Path fhirFolder = Paths.get("data", "fhir");

        if (!Files.exists(fhirFolder)) {
            throw new IOException(
                    "FHIR folder not found: " + fhirFolder.toAbsolutePath()
            );
        }

        int importedPatients = 0;

        try (var files = Files.list(fhirFolder)) {

            List<Path> jsonFiles = files
                    .filter(path -> path.toString().endsWith(".json"))
                    .toList();

            System.out.println(
                    "Found " + jsonFiles.size() + " FHIR JSON files."
            );

            for (Path file : jsonFiles) {

                try {

                    importSingleFile(file);

                    importedPatients++;

                    System.out.println(
                            "Imported patient " +
                            importedPatients +
                            " / " +
                            jsonFiles.size()
                    );

                } catch (Exception e) {

                    System.out.println(
                            "Failed to import: " +
                            file.getFileName()
                    );

                    System.out.println(
                            "Reason: " + e.getMessage()
                    );
                }
            }
        }

        System.out.println(
                "Finished importing " +
                importedPatients +
                " patient files."
        );

        return importedPatients;
    }

    private void importSingleFile(Path file) throws IOException {

        String json = Files.readString(file);

        Bundle bundle = fhirContext
                .newJsonParser()
                .parseResource(Bundle.class, json);

        PatientData patientData = new PatientData();

        List<Map<String, Object>> observations = new ArrayList<>();
        List<Map<String, Object>> conditions = new ArrayList<>();
        List<Map<String, Object>> medications = new ArrayList<>();
        List<Map<String, Object>> encounters = new ArrayList<>();
        List<Map<String, Object>> diagnosticReports = new ArrayList<>();

        for (Bundle.BundleEntryComponent entry : bundle.getEntry()) {

            Resource resource = entry.getResource();

            if (resource == null) {
                continue;
            }

            String resourceType =
                    resource.getResourceType().name();

            String resourceJson =
                    fhirContext
                            .newJsonParser()
                            .encodeResourceToString(resource);

            Map<String, Object> resourceMap =
                    objectMapper.readValue(
                            resourceJson,
                            new TypeReference<Map<String, Object>>() {}
                    );

            switch (resourceType) {

                case "Patient":

                    patientData.setId(
                            resource.getIdElement().getIdPart()
                    );

                    patientData.setPatient(resourceMap);

                    break;

                case "Observation":

                    observations.add(resourceMap);

                    break;

                case "Condition":

                    conditions.add(resourceMap);

                    break;

                case "MedicationRequest":

                    medications.add(resourceMap);

                    break;

                case "Encounter":

                    encounters.add(resourceMap);

                    break;

                case "DiagnosticReport":

                    diagnosticReports.add(resourceMap);

                    break;

                default:

                    // Other FHIR resources are currently ignored.
                    break;
            }
        }

        patientData.setObservations(observations);
        patientData.setConditions(conditions);
        patientData.setMedications(medications);
        patientData.setEncounters(encounters);
        patientData.setDiagnosticReports(diagnosticReports);

        if (patientData.getPatient() != null) {

            repository.save(patientData);
        }
    }
}