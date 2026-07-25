package com.vermeg.chatops.identity.dto;

import jakarta.validation.constraints.Size;

public record UserUpdateRequest(
        @Size(max = 160, message = "Display name must not exceed 160 characters")
        String displayName,
        Boolean active
) {
}