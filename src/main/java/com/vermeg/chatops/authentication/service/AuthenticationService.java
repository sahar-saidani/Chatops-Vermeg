package com.vermeg.chatops.authentication.service;

import com.vermeg.chatops.authentication.dto.ActivateAccountRequest;
import com.vermeg.chatops.authentication.dto.ForgotPasswordRequest;
import com.vermeg.chatops.authentication.dto.InviteUserRequest;
import com.vermeg.chatops.authentication.dto.LoginRequest;
import com.vermeg.chatops.authentication.dto.OneTimeTokenResponse;
import com.vermeg.chatops.authentication.dto.RefreshTokenRequest;
import com.vermeg.chatops.authentication.dto.ResetPasswordRequest;
import com.vermeg.chatops.authentication.dto.TokenResponse;

public interface AuthenticationService {

    OneTimeTokenResponse invite(InviteUserRequest request);

    TokenResponse activate(ActivateAccountRequest request);

    TokenResponse login(LoginRequest request);

    TokenResponse refresh(RefreshTokenRequest request);

    OneTimeTokenResponse forgotPassword(ForgotPasswordRequest request);

    TokenResponse resetPassword(ResetPasswordRequest request);
}