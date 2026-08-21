package com.brandanalyzer.controller;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.entity.User;
import com.brandanalyzer.repository.UserRepository;
import com.brandanalyzer.service.CacheService;
import com.brandanalyzer.service.PythonEngineClient;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AnalysisControllerTest {

    @Mock
    private CacheService cacheService;

    @Mock
    private PythonEngineClient pythonEngineClient;

    @Mock
    private UserRepository userRepository;

    @Mock
    private UserDetails userDetails;

    @InjectMocks
    private AnalysisController analysisController;

    @Test
    @DisplayName("Should return cached analysis JSON directly on cache hit without calling Python engine")
    void testAnalyze_CacheHit() {
        String brand = "Apple";
        String cachedJson = "{\"brand\":\"Apple\",\"cached\":true}";

        BrandReport report = new BrandReport();
        report.setBrandName(brand);
        report.setAnalysisData(cachedJson);

        when(cacheService.getCachedReport(brand)).thenReturn(Optional.of(report));

        ResponseEntity<String> response = analysisController.analyze(Map.of("brand", brand), userDetails);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(cachedJson, response.getBody());
        verifyNoInteractions(pythonEngineClient, userRepository);
        verify(cacheService, never()).saveReport(anyString(), any(), anyString());
    }

    @Test
    @DisplayName("Should invoke Python engine and save to DB on cache miss")
    void testAnalyze_CacheMiss() {
        String brand = "Apple";
        String freshJson = "{\"brand\":\"Apple\",\"cached\":false}";
        String username = "user1";

        User user = new User();
        user.setUsername(username);

        when(cacheService.getCachedReport(brand)).thenReturn(Optional.empty());
        when(pythonEngineClient.analyze(brand)).thenReturn(freshJson);
        when(userDetails.getUsername()).thenReturn(username);
        when(userRepository.findByUsername(username)).thenReturn(Optional.of(user));

        ResponseEntity<String> response = analysisController.analyze(Map.of("brand", brand), userDetails);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(freshJson, response.getBody());
        verify(pythonEngineClient).analyze(brand);
        verify(cacheService).saveReport(brand, user, freshJson);
    }
}
