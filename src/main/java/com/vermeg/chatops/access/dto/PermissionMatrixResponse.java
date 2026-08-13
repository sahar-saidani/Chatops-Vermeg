package com.vermeg.chatops.access.dto;

import java.util.List;
import java.util.UUID;

/**
 * Roles x permissions in one payload, so the UI can render the grid without
 * issuing a request per role.
 *
 * <p>Read-only. Assigning a permission to a role has no endpoint on this
 * backend -- role_permissions rows are created by the Flyway seeds -- so the
 * matrix reports the real grants rather than offering edits that would have
 * nowhere to go.
 */
public record PermissionMatrixResponse(
        List<PermissionResponse> permissions,
        List<RolePermissions> roles
) {

    /** One row of the grid: a role and the permission codes it actually grants. */
    public record RolePermissions(
            UUID id,
            String code,
            String name,
            boolean system,
            List<String> permissionCodes
    ) {
    }
}
