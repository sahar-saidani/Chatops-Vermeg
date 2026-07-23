package com.vermeg.chatops.authentication.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;
import java.util.UUID;

public record InviteUserRequest(
        @NotBlank(message = "Email is required") @Email(message = "Email must be valid") String email,
        @NotBlank(message = "Display name is required") @Size(max = 160, message = "Display name must not exceed 160 characters") String displayName,
        @NotNull(message = "Tenant is required") UUID tenantId,
        @NotEmpty(message = "At least one role is required") List<@NotNull UUID> roleIds
) {
}
