package com.vermeg.chatops.authentication.controller;

import com.vermeg.chatops.authentication.dto.ActivateAccountRequest;
import com.vermeg.chatops.authentication.dto.ForgotPasswordRequest;
import com.vermeg.chatops.authentication.dto.InviteUserRequest;
import com.vermeg.chatops.authentication.dto.LoginRequest;
import com.vermeg.chatops.authentication.dto.OneTimeTokenResponse;
import com.vermeg.chatops.authentication.dto.RefreshTokenRequest;
import com.vermeg.chatops.authentication.dto.ResetPasswordRequest;
import com.vermeg.chatops.authentication.dto.TokenResponse;
import com.vermeg.chatops.authentication.service.AuthenticationService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthenticationController {

    private final AuthenticationService authenticationService;

    public AuthenticationController(AuthenticationService authenticationService) {
        this.authenticationService = authenticationService;
    }

    @PostMapping("/invitations")
    @ResponseStatus(HttpStatus.CREATED)
    public OneTimeTokenResponse invite(@Valid @RequestBody InviteUserRequest request) {
        return authenticationService.invite(request);
    }

    @PostMapping("/activate")
    public TokenResponse activate(@Valid @RequestBody ActivateAccountRequest request) {
        return authenticationService.activate(request);
    }

    @PostMapping("/login")
    public TokenResponse login(@Valid @RequestBody LoginRequest request) {
        return authenticationService.login(request);
    }

    @PostMapping("/refresh")
    public TokenResponse refresh(@Valid @RequestBody RefreshTokenRequest request) {
        return authenticationService.refresh(request);
    }

    @PostMapping("/forgot-password")
    public OneTimeTokenResponse forgotPassword(@Valid @RequestBody ForgotPasswordRequest request) {
        return authenticationService.forgotPassword(request);
    }

    @PostMapping("/reset-password")
    public TokenResponse resetPassword(@Valid @RequestBody ResetPasswordRequest request) {
        return authenticationService.resetPassword(request);
    }
}