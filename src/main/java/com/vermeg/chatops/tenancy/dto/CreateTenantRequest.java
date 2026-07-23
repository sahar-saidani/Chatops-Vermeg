package com.vermeg.chatops.tenancy.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record CreateTenantRequest(
        @NotBlank(message = "Tenant code is required")
        @Size(max = 64, message = "Tenant code must not exceed 64 characters")
        @Pattern(regexp = "[A-Za-z0-9_-]+", message = "Tenant code may contain only letters, digits, underscores, and hyphens")
        String code,
        @NotBlank(message = "Tenant name is required")
        @Size(max = 160, message = "Tenant name must not exceed 160 characters")
        String name
) {
}
