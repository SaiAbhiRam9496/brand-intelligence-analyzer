package com.brandanalyzer.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;

class JwtUtilTest {

    private JwtUtil jwtUtil;
    private final String secret = "abcdefghijklmnopqrstuvwxyz12345678901234567890"; // 256+ bit key
    private final long expirationMs = 3600000; // 1 hour

    @BeforeEach
    void setUp() {
        jwtUtil = new JwtUtil();
        ReflectionTestUtils.setField(jwtUtil, "secret", secret);
        ReflectionTestUtils.setField(jwtUtil, "expirationMs", expirationMs);
    }

    @Test
    @DisplayName("Should generate valid token and extract username correctly")
    void testGenerateAndExtractToken() {
        String username = "testuser";
        String token = jwtUtil.generateToken(username);

        assertNotNull(token);
        assertTrue(jwtUtil.isTokenValid(token));
        assertEquals(username, jwtUtil.extractUsername(token));
    }

    @Test
    @DisplayName("Should reject malformed JWT token")
    void testInvalidTokenSignatureOrFormat() {
        String invalidToken = "not.a.real.jwt.token";
        assertFalse(jwtUtil.isTokenValid(invalidToken));
    }

    @Test
    @DisplayName("Should reject expired JWT token")
    void testExpiredTokenRejection() {
        // Set short expiration of -1000ms (already expired)
        ReflectionTestUtils.setField(jwtUtil, "expirationMs", -1000L);
        String token = jwtUtil.generateToken("expiredUser");

        assertFalse(jwtUtil.isTokenValid(token));
    }

    @Test
    @DisplayName("Should reject token signed with different secret key")
    void testTokenWithDifferentSecretKey() {
        String token = jwtUtil.generateToken("user1");

        JwtUtil anotherJwtUtil = new JwtUtil();
        ReflectionTestUtils.setField(anotherJwtUtil, "secret", "differentSecretKey123456789012345678901234567890");
        ReflectionTestUtils.setField(anotherJwtUtil, "expirationMs", expirationMs);

        assertFalse(anotherJwtUtil.isTokenValid(token));
    }
}
