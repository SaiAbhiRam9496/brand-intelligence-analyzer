package com.brandanalyzer.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class PythonEngineClient {

    @Value("${python.engine.url}")
    private String pythonEngineUrl;

    private final RestTemplate restTemplate;

    /**
     * Calls the python-engine /analyze endpoint and returns the raw JSON string.
     */
    public String analyze(String brandName) {
        String url = pythonEngineUrl + "/analyze";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, String>> request = new HttpEntity<>(Map.of("brand", brandName), headers);

        ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);
        if (response.getStatusCode().is2xxSuccessful()) {
            return response.getBody();
        }
        throw new RuntimeException("Python engine returned error: " + response.getStatusCode());
    }

    /**
     * Calls the python-engine /generate-pdf endpoint and returns the PDF bytes.
     */
    public byte[] generatePdf(String brandName, String analysisJson) {
        String url = pythonEngineUrl + "/generate-pdf";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        String body = String.format("{\"brand\":\"%s\",\"analysis_data\":%s}", brandName, analysisJson);
        HttpEntity<String> request = new HttpEntity<>(body, headers);

        ResponseEntity<byte[]> response = restTemplate.postForEntity(url, request, byte[].class);
        if (response.getStatusCode().is2xxSuccessful()) {
            return response.getBody();
        }
        throw new RuntimeException("Python engine PDF generation failed: " + response.getStatusCode());
    }
}
