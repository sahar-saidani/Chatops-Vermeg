package com.vermeg.chatops.tenancy.dto;

import java.time.Instant;
import java.util.UUID;

public record TenantResponse(
        UUID id,
        String code,
        String name,
        boolean active,
        Instant createdAt,
        Instant updatedAt
) {
}
