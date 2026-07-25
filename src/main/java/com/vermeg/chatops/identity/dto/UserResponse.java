package com.vermeg.chatops.identity.dto;

import com.vermeg.chatops.identity.entity.UserStatus;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record UserResponse(
        UUID id,
        String email,
        String displayName,
        UserStatus status,
        Instant createdAt,
        List<UserMembershipSummary> memberships
) {
}