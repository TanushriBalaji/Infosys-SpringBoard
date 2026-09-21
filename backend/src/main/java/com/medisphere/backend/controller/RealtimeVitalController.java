package com.medisphere.backend.controller;

import com.medisphere.backend.model.PatientData;
import com.medisphere.backend.model.RealtimeVital;
import com.medisphere.backend.repository.PatientDataRepository;
import com.medisphere.backend.repository.RealtimeVitalRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/realtime-vitals")
@CrossOrigin(origins = {"http://localhost:4200", "http://127.0.0.1:4200"})
public class RealtimeVitalController {

    private final RealtimeVitalRepository realtimeVitalRepository;
    private final PatientDataRepository patientDataRepository;

    public RealtimeVitalController(RealtimeVitalRepository realtimeVitalRepository, PatientDataRepository patientDataRepository) {
        this.realtimeVitalRepository = realtimeVitalRepository;
        this.patientDataRepository = patientDataRepository;
    }

    @GetMapping("/patient/{patientId}/latest")
    public ResponseEntity<RealtimeVital> getLatestVitals(@PathVariable String patientId) {
        return realtimeVitalRepository.findFirstByPatientIdOrderByTimestampDesc(patientId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.noContent().build());
    }

    @GetMapping("/patient/{patientId}/history")
    public List<RealtimeVital> getVitalsHistory(@PathVariable String patientId) {
        List<RealtimeVital> history = realtimeVitalRepository.findTop100ByPatientIdOrderByTimestampDesc(patientId);
        // Reverse so that chart receives chronological order (oldest to newest)
        Collections.reverse(history);
        return history;
    }

    @GetMapping("/patients")
    public List<Map<String, String>> getPatientList() {
        List<PatientData> allPatients = patientDataRepository.findAll();
        List<Map<String, String>> patientList = new ArrayList<>();

        for (PatientData pd : allPatients) {
            Map<String, String> entry = new HashMap<>();
            entry.put("id", pd.getId());

            String name = "Unknown";
            if (pd.getPatient() != null) {
                Object nameObj = pd.getPatient().get("name");
                if (nameObj instanceof List<?> list && !list.isEmpty()) {
                    Object firstItem = list.get(0);
                    if (firstItem instanceof Map<?, ?> map) {
                        Object givenObj = map.get("given");
                        String given = "";
                        if (givenObj instanceof List<?> gList) {
                            given = String.join(" ", gList.stream().map(Object::toString).toList());
                        } else if (givenObj != null) {
                            given = givenObj.toString();
                        }
                        String family = map.get("family") != null ? map.get("family").toString() : "";
                        name = (given + " " + family).trim();
                    }
                }
            }
            entry.put("name", name);
            patientList.add(entry);
        }

        return patientList;
    }
}
