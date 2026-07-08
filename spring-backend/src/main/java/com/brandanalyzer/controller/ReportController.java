package com.brandanalyzer.controller;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.repository.BrandReportRepository;
import com.brandanalyzer.repository.UserRepository;
import com.brandanalyzer.service.PythonEngineClient;
import lombok.RequiredArgsConstructor;
import org.springframework.http.*;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reports")
@RequiredArgsConstructor
public class ReportController {

    private final BrandReportRepository reportRepository;
    private final UserRepository userRepository;
    private final PythonEngineClient pythonEngineClient;

    /**
     * Returns all past reports for the authenticated user.
     */
    @GetMapping("/history")
    public ResponseEntity<List<Map<String, Object>>> getHistory(@AuthenticationPrincipal UserDetails userDetails) {
        var user = userRepository.findByUsername(userDetails.getUsername()).orElseThrow();
        List<BrandReport> reports = reportRepository.findByRequestedByOrderByCreatedAtDesc(user);

        List<Map<String, Object>> result = reports.stream().map(r -> {
                Map<String, Object> entry = new java.util.HashMap<>();
                entry.put("id", r.getId());
                entry.put("brandName", r.getBrandName());
                entry.put("createdAt", r.getCreatedAt().toString());
                return entry;
        }).toList();

        return ResponseEntity.ok(result);
    }

    /**
     * Generates and streams a PDF report for the given brand report ID.
     */
    @GetMapping("/{id}/pdf")
    public ResponseEntity<byte[]> downloadPdf(@PathVariable Long id,
                                              @AuthenticationPrincipal UserDetails userDetails) {
        BrandReport report = reportRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Report not found"));

        byte[] pdf = pythonEngineClient.generatePdf(report.getBrandName(), report.getAnalysisData());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDispositionFormData("attachment", report.getBrandName() + "_Report.pdf");

        return new ResponseEntity<>(pdf, headers, HttpStatus.OK);
    }
}
