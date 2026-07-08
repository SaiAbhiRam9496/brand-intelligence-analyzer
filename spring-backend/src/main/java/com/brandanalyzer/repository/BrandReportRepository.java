package com.brandanalyzer.repository;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface BrandReportRepository extends JpaRepository<BrandReport, Long> {
    List<BrandReport> findByRequestedByOrderByCreatedAtDesc(User user);
    Optional<BrandReport> findTopByBrandNameIgnoreCaseAndCreatedAtAfterOrderByCreatedAtDesc(
        String brandName, LocalDateTime after
    );
}
