package com.brandanalyzer.controller;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.entity.User;
import com.brandanalyzer.repository.BrandReportRepository;
import com.brandanalyzer.repository.UserRepository;
import com.brandanalyzer.service.PythonEngineClient;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.userdetails.UserDetails;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ReportControllerTest {

    @Mock
    private BrandReportRepository reportRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private PythonEngineClient pythonEngineClient;

    @Mock
    private UserDetails userDetails;

    @InjectMocks
    private ReportController reportController;

    @Test
    @DisplayName("Should return list of history report metadata for authenticated user")
    void testGetHistory_Success() {
        String username = "sam";
        User user = new User();
        user.setUsername(username);

        BrandReport report1 = new BrandReport();
        report1.setId(1L);
        report1.setBrandName("Nike");
        report1.setCreatedAt(LocalDateTime.of(2026, 8, 20, 10, 0));

        when(userDetails.getUsername()).thenReturn(username);
        when(userRepository.findByUsername(username)).thenReturn(Optional.of(user));
        when(reportRepository.findByRequestedByOrderByCreatedAtDesc(user)).thenReturn(List.of(report1));

        ResponseEntity<List<Map<String, Object>>> response = reportController.getHistory(userDetails);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().size());
        assertEquals(1L, response.getBody().get(0).get("id"));
        assertEquals("Nike", response.getBody().get(0).get("brandName"));
    }

    @Test
    @DisplayName("Should download and stream PDF report successfully")
    void testDownloadPdf_Success() {
        Long reportId = 42L;
        BrandReport report = new BrandReport();
        report.setId(reportId);
        report.setBrandName("Samsung");
        report.setAnalysisData("{\"data\":\"test\"}");

        byte[] mockPdfBytes = new byte[]{1, 2, 3, 4};

        when(reportRepository.findById(reportId)).thenReturn(Optional.of(report));
        when(pythonEngineClient.generatePdf("Samsung", "{\"data\":\"test\"}")).thenReturn(mockPdfBytes);

        ResponseEntity<byte[]> response = reportController.downloadPdf(reportId, userDetails);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(MediaType.APPLICATION_PDF, response.getHeaders().getContentType());
        assertArrayEquals(mockPdfBytes, response.getBody());
    }

    @Test
    @DisplayName("Should throw RuntimeException when PDF requested for non-existent report ID")
    void testDownloadPdf_ReportNotFound() {
        Long reportId = 99L;
        when(reportRepository.findById(reportId)).thenReturn(Optional.empty());

        RuntimeException ex = assertThrows(RuntimeException.class,
                () -> reportController.downloadPdf(reportId, userDetails));
        assertEquals("Report not found", ex.getMessage());
        verifyNoInteractions(pythonEngineClient);
    }
}
