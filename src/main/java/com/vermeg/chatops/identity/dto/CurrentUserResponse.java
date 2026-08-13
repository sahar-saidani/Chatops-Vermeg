package com.vermeg.chatops.identity.dto;

import com.vermeg.chatops.identity.entity.UserStatus;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

/**
 * The authenticated caller's own profile.
 *
 * <p>Added because roles and permissions previously existed only inside the
 * server-side {@code Authentication} object: the login response carries a JWT
 * whose only claim is the subject, so a browser client had no way to discover
 * what the signed-in user is allowed to do. Exposing them here keeps the
 * frontend's guards driven by the real, DB-backed RBAC model instead of
 * guessing from the email address.
 */
public record CurrentUserResponse(
        UUID id,
        String email,
        String displayName,
        UserStatus status,
        Instant createdAt,
        List<UserMembershipSummary> memberships,
        List<String> roles,
        List<String> permissions
) {
}
