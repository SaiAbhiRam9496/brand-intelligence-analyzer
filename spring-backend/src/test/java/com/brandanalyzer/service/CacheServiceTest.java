package com.brandanalyzer.service;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.entity.User;
import com.brandanalyzer.repository.BrandReportRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CacheServiceTest {

    @Mock
    private BrandReportRepository reportRepository;

    @InjectMocks
    private CacheService cacheService;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(cacheService, "freshnessDays", 2);
    }

    @Test
    @DisplayName("Should return cached report when a fresh report exists within 2 days")
    void testGetCachedReport_CacheHit() {
        String brandName = "Nike";
        BrandReport cachedReport = new BrandReport();
        cachedReport.setBrandName("Nike");
        cachedReport.setAnalysisData("{\"sentiment\":\"positive\"}");

        when(reportRepository.findTopByBrandNameIgnoreCaseAndCreatedAtAfterOrderByCreatedAtDesc(
                eq(brandName), any(LocalDateTime.class)))
                .thenReturn(Optional.of(cachedReport));

        Optional<BrandReport> result = cacheService.getCachedReport(brandName);

        assertTrue(result.isPresent());
        assertEquals("{\"sentiment\":\"positive\"}", result.get().getAnalysisData());
    }

    @Test
    @DisplayName("Should return empty Optional on cache miss (no recent report)")
    void testGetCachedReport_CacheMiss() {
        String brandName = "Adidas";

        when(reportRepository.findTopByBrandNameIgnoreCaseAndCreatedAtAfterOrderByCreatedAtDesc(
                eq(brandName), any(LocalDateTime.class)))
                .thenReturn(Optional.empty());

        Optional<BrandReport> result = cacheService.getCachedReport(brandName);

        assertFalse(result.isPresent());
    }

    @Test
    @DisplayName("Should verify freshness cutoff timestamp calculation uses freshnessDays property")
    void testGetCachedReport_CutoffTimeWindow() {
        String brandName = "Puma";
        ArgumentCaptor<LocalDateTime> cutoffCaptor = ArgumentCaptor.forClass(LocalDateTime.class);

        when(reportRepository.findTopByBrandNameIgnoreCaseAndCreatedAtAfterOrderByCreatedAtDesc(
                eq(brandName), cutoffCaptor.capture()))
                .thenReturn(Optional.empty());

        LocalDateTime beforeCall = LocalDateTime.now().minusDays(2).minusSeconds(5);
        cacheService.getCachedReport(brandName);
        LocalDateTime afterCall = LocalDateTime.now().minusDays(2).plusSeconds(5);

        LocalDateTime capturedCutoff = cutoffCaptor.getValue();
        assertTrue(capturedCutoff.isAfter(beforeCall) && capturedCutoff.isBefore(afterCall));
    }

    @Test
    @DisplayName("Should save brand report to repository correctly")
    void testSaveReport() {
        User user = new User();
        user.setUsername("john");

        BrandReport expectedSaved = new BrandReport();
        expectedSaved.setBrandName("Nike");
        expectedSaved.setRequestedBy(user);
        expectedSaved.setAnalysisData("{\"score\": 95}");

        when(reportRepository.save(any(BrandReport.class))).thenReturn(expectedSaved);

        BrandReport result = cacheService.saveReport("Nike", user, "{\"score\": 95}");

        assertNotNull(result);
        assertEquals("Nike", result.getBrandName());
        assertEquals(user, result.getRequestedBy());
        assertEquals("{\"score\": 95}", result.getAnalysisData());

        ArgumentCaptor<BrandReport> captor = ArgumentCaptor.forClass(BrandReport.class);
        verify(reportRepository).save(captor.capture());
        BrandReport savedEntity = captor.getValue();
        assertEquals("Nike", savedEntity.getBrandName());
        assertEquals(user, savedEntity.getRequestedBy());
        assertEquals("{\"score\": 95}", savedEntity.getAnalysisData());
    }
}
