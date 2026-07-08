package com.brandanalyzer.service;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.entity.User;
import com.brandanalyzer.repository.BrandReportRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class CacheService {

    private final BrandReportRepository reportRepository;

    @Value("${cache.freshness.days}")
    private int freshnessDays;

    /**
     * Returns a cached report if one exists within the freshness window.
     */
    public Optional<BrandReport> getCachedReport(String brandName) {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(freshnessDays);
        return reportRepository.findTopByBrandNameIgnoreCaseAndCreatedAtAfterOrderByCreatedAtDesc(brandName, cutoff);
    }

    /**
     * Saves a new report to the database.
     */
    public BrandReport saveReport(String brandName, User user, String analysisJson) {
        BrandReport report = new BrandReport();
        report.setBrandName(brandName);
        report.setRequestedBy(user);
        report.setAnalysisData(analysisJson);
        return reportRepository.save(report);
    }
}
