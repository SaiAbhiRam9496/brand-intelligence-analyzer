package com.brandanalyzer.exception;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class GlobalExceptionHandlerTest {

    private GlobalExceptionHandler exceptionHandler;

    @BeforeEach
    void setUp() {
        exceptionHandler = new GlobalExceptionHandler();
    }

    @Test
    @DisplayName("Should handle IllegalArgumentException with 400 Bad Request and error message")
    void testHandleIllegalArg() {
        IllegalArgumentException ex = new IllegalArgumentException("Username already taken.");

        ResponseEntity<Map<String, String>> response = exceptionHandler.handleIllegalArg(ex);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("Username already taken.", response.getBody().get("error"));
    }

    @Test
    @DisplayName("Should handle BadCredentialsException with 401 Unauthorized")
    void testHandleBadCreds() {
        BadCredentialsException ex = new BadCredentialsException("Bad credentials");

        ResponseEntity<Map<String, String>> response = exceptionHandler.handleBadCreds(ex);

        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("Invalid username or password.", response.getBody().get("error"));
    }

    @Test
    @DisplayName("Should handle RuntimeException with 500 Internal Server Error")
    void testHandleRuntime() {
        RuntimeException ex = new RuntimeException("Python engine returned error: 500 INTERNAL_SERVER_ERROR");

        ResponseEntity<Map<String, String>> response = exceptionHandler.handleRuntime(ex);

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("Python engine returned error: 500 INTERNAL_SERVER_ERROR", response.getBody().get("error"));
    }
}
