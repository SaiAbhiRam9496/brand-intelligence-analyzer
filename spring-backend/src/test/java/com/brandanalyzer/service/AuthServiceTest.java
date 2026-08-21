package com.brandanalyzer.service;

import com.brandanalyzer.entity.User;
import com.brandanalyzer.repository.UserRepository;
import com.brandanalyzer.security.JwtUtil;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtUtil jwtUtil;

    @Mock
    private AuthenticationManager authManager;

    @Mock
    private UserDetailsService userDetailsService;

    @InjectMocks
    private AuthService authService;

    @Test
    @DisplayName("Should successfully register new user with hashed password and return JWT")
    void testRegister_Success() {
        String username = "newuser";
        String rawPassword = "password123";
        String encodedPassword = "encoded_password_hash";
        String token = "jwt_token_abc";

        when(userRepository.existsByUsername(username)).thenReturn(false);
        when(passwordEncoder.encode(rawPassword)).thenReturn(encodedPassword);
        when(jwtUtil.generateToken(username)).thenReturn(token);

        String resultToken = authService.register(username, rawPassword);

        assertEquals(token, resultToken);

        ArgumentCaptor<User> userCaptor = ArgumentCaptor.forClass(User.class);
        verify(userRepository).save(userCaptor.capture());
        User savedUser = userCaptor.getValue();
        assertEquals(username, savedUser.getUsername());
        assertEquals(encodedPassword, savedUser.getPasswordHash());
    }

    @Test
    @DisplayName("Should throw IllegalArgumentException when registering duplicate username")
    void testRegister_DuplicateUsername() {
        String username = "existinguser";
        when(userRepository.existsByUsername(username)).thenReturn(true);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> authService.register(username, "pass"));
        assertEquals("Username already taken.", ex.getMessage());
        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("Should successfully login user with correct credentials and return JWT")
    void testLogin_Success() {
        String username = "validuser";
        String password = "correctpassword";
        String token = "jwt_login_token";

        UserDetails userDetails = new org.springframework.security.core.userdetails.User(
                username, password, Collections.emptyList());

        when(userDetailsService.loadUserByUsername(username)).thenReturn(userDetails);
        when(jwtUtil.generateToken(username)).thenReturn(token);

        String resultToken = authService.login(username, password);

        assertEquals(token, resultToken);
        verify(authManager).authenticate(any(UsernamePasswordAuthenticationToken.class));
    }

    @Test
    @DisplayName("Should propagate BadCredentialsException when login fails authentication")
    void testLogin_Failure() {
        String username = "validuser";
        String wrongPassword = "wrongpassword";

        doThrow(new BadCredentialsException("Bad credentials"))
                .when(authManager).authenticate(any(UsernamePasswordAuthenticationToken.class));

        assertThrows(BadCredentialsException.class, () -> authService.login(username, wrongPassword));
        verify(userDetailsService, never()).loadUserByUsername(anyString());
    }
}
