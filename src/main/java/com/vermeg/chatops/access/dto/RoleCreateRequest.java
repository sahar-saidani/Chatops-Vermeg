package com.vermeg.chatops.access.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RoleCreateRequest(
        @NotBlank(message = "Role code is required")
        @Size(max = 100, message = "Role code must not exceed 100 characters")
        @Pattern(regexp = "[A-Za-z0-9_-]+", message = "Role code may contain only letters, digits, underscores, and hyphens")
        String code,
        @NotBlank(message = "Role name is required")
        @Size(max = 120, message = "Role name must not exceed 120 characters")
        String name,
        @Size(max = 500, message = "Role description must not exceed 500 characters")
        String description
) {
}