package com.vermeg.chatops.authentication.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RefreshTokenRequest(
        @NotBlank(message = "Refresh token is required") @Size(max = 512, message = "Refresh token is invalid") String refreshToken
) {
}
