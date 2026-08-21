package com.brandanalyzer.controller;

import com.brandanalyzer.service.AuthService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    @Mock
    private AuthService authService;

    @InjectMocks
    private AuthController authController;

    @Test
    @DisplayName("Should return 200 OK with token on successful user registration")
    void testRegister_Success() {
        Map<String, String> body = Map.of("username", "bob", "password", "secr3t");
        when(authService.register("bob", "secr3t")).thenReturn("token_123");

        ResponseEntity<Map<String, String>> response = authController.register(body);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("token_123", response.getBody().get("token"));
        verify(authService).register("bob", "secr3t");
    }

    @Test
    @DisplayName("Should return 200 OK with token on successful user login")
    void testLogin_Success() {
        Map<String, String> body = Map.of("username", "bob", "password", "secr3t");
        when(authService.login("bob", "secr3t")).thenReturn("token_456");

        ResponseEntity<Map<String, String>> response = authController.login(body);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("token_456", response.getBody().get("token"));
        verify(authService).login("bob", "secr3t");
    }

    @Test
    @DisplayName("Should propagate exception when authService.register fails")
    void testRegister_Failure() {
        Map<String, String> body = Map.of("username", "existing", "password", "pass");
        when(authService.register("existing", "pass")).thenThrow(new IllegalArgumentException("Username already taken."));

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class, () -> authController.register(body));
        assertEquals("Username already taken.", ex.getMessage());
    }
}
