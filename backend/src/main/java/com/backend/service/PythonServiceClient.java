package com.backend.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class PythonServiceClient {

    private final RestTemplate restTemplate;

    @Value("${python.service.url:http://localhost:8000}")
    private String pythonServiceUrl;

    public PythonServiceClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public String generateStudyGuide(List<MultipartFile> pdfs, String sourcesJson) {
        String url = pythonServiceUrl + "/api/get-output";
        log.info("Calling Python microservice at: {}", url);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

        if (pdfs != null) {
            for (MultipartFile pdf : pdfs) {
                try {
                    byte[] bytes = pdf.getBytes();
                    String filename = pdf.getOriginalFilename();
                    ByteArrayResource resource = new ByteArrayResource(bytes) {
                        @Override
                        public String getFilename() {
                            return filename;
                        }
                    };
                    body.add("pdfs", resource);
                } catch (IOException e) {
                    log.error("Failed to read PDF: {}", pdf.getOriginalFilename(), e);
                }
            }
        }

        if (sourcesJson != null) {
            body.add("sources", sourcesJson);
        }

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestEntity, Map.class);
            if (response.getBody() != null && response.getBody().containsKey("study_guide")) {
                String guide = (String) response.getBody().get("study_guide");
                log.info("Received study guide from Python service ({} chars)", guide.length());
                return guide;
            }
            throw new RuntimeException("Python service returned no study_guide field");
        } catch (Exception e) {
            log.error("Error calling Python microservice", e);
            throw new RuntimeException("Failed to generate study guide: " + e.getMessage(), e);
        }
    }
}
