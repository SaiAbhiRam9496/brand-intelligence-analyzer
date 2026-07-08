package com.brandanalyzer.controller;

import com.brandanalyzer.entity.BrandReport;
import com.brandanalyzer.entity.User;
import com.brandanalyzer.repository.UserRepository;
import com.brandanalyzer.service.CacheService;
import com.brandanalyzer.service.PythonEngineClient;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
public class AnalysisController {

    private final CacheService cacheService;
    private final PythonEngineClient pythonEngineClient;
    private final UserRepository userRepository;

    @PostMapping("/analyze")
    public ResponseEntity<String> analyze(@RequestBody Map<String, String> body,
                                          @AuthenticationPrincipal UserDetails userDetails) {
        String brandName = body.get("brand");

        // Check cache first
        Optional<BrandReport> cached = cacheService.getCachedReport(brandName);
        if (cached.isPresent()) {
            return ResponseEntity.ok(cached.get().getAnalysisData());
        }

        // Call python engine
        String analysisJson = pythonEngineClient.analyze(brandName);

        // Save to DB
        User user = userRepository.findByUsername(userDetails.getUsername()).orElseThrow();
        cacheService.saveReport(brandName, user, analysisJson);

        return ResponseEntity.ok(analysisJson);
    }
}
