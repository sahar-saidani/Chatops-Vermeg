package com.vermeg.chatops.tenancy.dto;

import com.vermeg.chatops.tenancy.entity.EnvironmentType;

import java.time.Instant;
import java.util.UUID;

public record EnvironmentResponse(
        UUID id,
        String name,
        EnvironmentType type,
        TenantSummaryResponse tenant,
        Instant createdAt,
        Instant updatedAt
) {
}
