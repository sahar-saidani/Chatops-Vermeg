package com.vermeg.chatops.access.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record PermissionCreateRequest(
        @NotBlank(message = "Permission code is required")
        @Size(max = 100, message = "Permission code must not exceed 100 characters")
        @Pattern(regexp = "[A-Za-z0-9_-]+", message = "Permission code may contain only letters, digits, underscores, and hyphens")
        String code,
        @NotBlank(message = "Permission name is required")
        @Size(max = 120, message = "Permission name must not exceed 120 characters")
        String name,
        @Size(max = 500, message = "Permission description must not exceed 500 characters")
        String description
) {
}