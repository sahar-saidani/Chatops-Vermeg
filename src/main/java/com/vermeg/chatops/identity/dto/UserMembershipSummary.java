package com.vermeg.chatops.identity.dto;

import java.util.UUID;

public record UserMembershipSummary(
        UUID tenantId,
        String tenantCode,
        String tenantName,
        boolean active
) {
}