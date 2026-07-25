package com.vermeg.chatops.access.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RoleUpdateRequest(
        @NotBlank(message = "Role name is required")
        @Size(max = 120, message = "Role name must not exceed 120 characters")
        String name,
        @Size(max = 500, message = "Role description must not exceed 500 characters")
        String description
) {
}