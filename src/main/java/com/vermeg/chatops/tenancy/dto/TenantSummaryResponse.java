package com.vermeg.chatops.tenancy.dto;

import java.util.UUID;

/**
 * Minimal tenant information embedded in an {@link EnvironmentResponse}.
 * If a fuller TenantResponse DTO already exists elsewhere in the project,
 * this can be swapped out for it - kept separate here to avoid guessing its
 * shape.
 */
public record TenantSummaryResponse(
        UUID id,
        String name
) {
}
