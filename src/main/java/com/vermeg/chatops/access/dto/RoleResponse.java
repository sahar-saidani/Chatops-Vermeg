package com.vermeg.chatops.access.dto;

import java.time.Instant;
import java.util.UUID;

public record RoleResponse(
        UUID id,
        String code,
        String name,
        String description,
        boolean system,
        Instant createdAt,
        Instant updatedAt
) {
}