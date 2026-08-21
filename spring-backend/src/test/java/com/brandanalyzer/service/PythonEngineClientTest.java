package com.brandanalyzer.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PythonEngineClientTest {

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private PythonEngineClient pythonEngineClient;

    private final String baseUrl = "http://localhost:8000";

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(pythonEngineClient, "pythonEngineUrl", baseUrl);
    }

    @Test
    @DisplayName("Should return raw JSON string on successful /analyze call")
    void testAnalyze_Success() {
        String brand = "Tesla";
        String mockResponseJson = "{\"brand\":\"Tesla\",\"sentiment\":{\"positive\":80}}";

        ResponseEntity<String> responseEntity = new ResponseEntity<>(mockResponseJson, HttpStatus.OK);
        when(restTemplate.postForEntity(eq(baseUrl + "/analyze"), any(HttpEntity.class), eq(String.class)))
                .thenReturn(responseEntity);

        String result = pythonEngineClient.analyze(brand);

        assertEquals(mockResponseJson, result);

        @SuppressWarnings("unchecked")
        ArgumentCaptor<HttpEntity<Map<String, String>>> requestCaptor = ArgumentCaptor.forClass(HttpEntity.class);
        verify(restTemplate).postForEntity(eq(baseUrl + "/analyze"), requestCaptor.capture(), eq(String.class));
        assertEquals("Tesla", requestCaptor.getValue().getBody().get("brand"));
    }

    @Test
    @DisplayName("Should throw RuntimeException when /analyze HTTP call returns non-2xx status")
    void testAnalyze_Non2xxFailure() {
        ResponseEntity<String> responseEntity = new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        when(restTemplate.postForEntity(eq(baseUrl + "/analyze"), any(HttpEntity.class), eq(String.class)))
                .thenReturn(responseEntity);

        RuntimeException ex = assertThrows(RuntimeException.class, () -> pythonEngineClient.analyze("Tesla"));
        assertTrue(ex.getMessage().contains("Python engine returned error"));
    }

    @Test
    @DisplayName("Should return byte array on successful /generate-pdf call")
    void testGeneratePdf_Success() {
        String brand = "Nike";
        String json = "{\"data\":\"test\"}";
        byte[] expectedBytes = new byte[]{1, 2, 3, 4, 5};

        ResponseEntity<byte[]> responseEntity = new ResponseEntity<>(expectedBytes, HttpStatus.OK);
        when(restTemplate.postForEntity(eq(baseUrl + "/generate-pdf"), any(HttpEntity.class), eq(byte[].class)))
                .thenReturn(responseEntity);

        byte[] resultBytes = pythonEngineClient.generatePdf(brand, json);

        assertArrayEquals(expectedBytes, resultBytes);

        @SuppressWarnings("unchecked")
        ArgumentCaptor<HttpEntity<String>> requestCaptor = ArgumentCaptor.forClass(HttpEntity.class);
        verify(restTemplate).postForEntity(eq(baseUrl + "/generate-pdf"), requestCaptor.capture(), eq(byte[].class));
        assertTrue(requestCaptor.getValue().getBody().contains("\"brand\":\"Nike\""));
    }

    @Test
    @DisplayName("Should throw RuntimeException when /generate-pdf HTTP call returns non-2xx status")
    void testGeneratePdf_Non2xxFailure() {
        ResponseEntity<byte[]> responseEntity = new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        when(restTemplate.postForEntity(eq(baseUrl + "/generate-pdf"), any(HttpEntity.class), eq(byte[].class)))
                .thenReturn(responseEntity);

        RuntimeException ex = assertThrows(RuntimeException.class,
                () -> pythonEngineClient.generatePdf("Nike", "{}"));
        assertTrue(ex.getMessage().contains("Python engine PDF generation failed"));
    }
}
