package com.vermeg.chatops.authentication.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LoginRequest(
        @NotBlank(message = "Email is required") @Email(message = "Email must be valid") String email,
        @NotBlank(message = "Password is required") @Size(max = 128, message = "Password must not exceed 128 characters") String password
) {
}
