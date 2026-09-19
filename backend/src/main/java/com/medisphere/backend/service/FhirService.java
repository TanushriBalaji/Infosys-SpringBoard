package com.medisphere.backend.service;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.rest.client.api.IGenericClient;
import org.hl7.fhir.r4.model.Bundle;
import org.hl7.fhir.r4.model.Patient;
import org.springframework.stereotype.Service;

@Service
public class FhirService {

    private final FhirContext fhirContext;
    private final IGenericClient client;

    public FhirService() {

        // Create a FHIR R4 context
        fhirContext = FhirContext.forR4();

        // Connect to the HAPI FHIR R4 server
        client = fhirContext.newRestfulGenericClient(
                "https://hapi.fhir.org/baseR4"
        );
    }

    public String getPatients() {

        // Search for Patient resources
        Bundle bundle = client
                .search()
                .forResource(Patient.class)
                .count(5)
                .returnBundle(Bundle.class)
                .execute();

        StringBuilder result = new StringBuilder();

        // Process each patient
        for (Bundle.BundleEntryComponent entry : bundle.getEntry()) {

            Patient patient = (Patient) entry.getResource();

            result.append("Patient ID: ")
                    .append(patient.getIdElement().getIdPart())
                    .append("\n");

            if (patient.hasName()) {

                result.append("Name: ")
                        .append(
                                patient.getNameFirstRep()
                                        .getNameAsSingleString()
                        )
                        .append("\n");
            }

            result.append("--------------------\n");
        }

        return result.toString();
    }
}