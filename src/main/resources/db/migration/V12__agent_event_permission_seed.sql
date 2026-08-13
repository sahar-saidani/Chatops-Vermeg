-- Permissions for reading agent reports out of canonical_events.
--
-- Two distinct scopes, because canonical_events holds every tenant's data in
-- one table and a single permission cannot express "which tenants":
--
--   AGENT_EVENT_READ     - read agent reports for the tenants the caller is
--                          actually a member of. Granted to ADMIN and
--                          OPERATOR; V3 describes OPERATOR as the role that
--                          "operates agents and monitors executions", which is
--                          exactly this endpoint.
--   AGENT_EVENT_READ_ALL - read every tenant's reports, including legacy rows
--                          whose tenant column was never populated. Granted to
--                          ADMIN only.
--
-- The platform-wide scope is a separate permission rather than an implicit
-- "role code is ADMIN" check in Java: roles are database rows that an operator
-- can rename or recreate, so hardcoding a role name would silently grant or
-- revoke cross-tenant access as the RBAC data changes. Making it a permission
-- keeps the decision in the same table as every other authorization rule.
INSERT INTO permissions (id, created_at, updated_at, code, name, description)
SELECT
    'b0000000-0000-0000-0000-000000000010',
    now(),
    now(),
    'AGENT_EVENT_READ',
    'Read agent events',
    'Allows viewing the reports collected by the git, jenkins, installation, log and infrastructure agents'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'AGENT_EVENT_READ');

INSERT INTO role_permissions (id, created_at, updated_at, role_id, permission_id)
SELECT
    'c0000000-0000-0000-0000-000000000010',
    now(),
    now(),
    'a0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000010'
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions
    WHERE role_id = 'a0000000-0000-0000-0000-000000000001'
      AND permission_id = 'b0000000-0000-0000-0000-000000000010'
);

INSERT INTO role_permissions (id, created_at, updated_at, role_id, permission_id)
SELECT
    'c0000000-0000-0000-0000-000000000011',
    now(),
    now(),
    'a0000000-0000-0000-0000-000000000004',
    'b0000000-0000-0000-0000-000000000010'
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions
    WHERE role_id = 'a0000000-0000-0000-0000-000000000004'
      AND permission_id = 'b0000000-0000-0000-0000-000000000010'
);

-- Platform-wide scope.
INSERT INTO permissions (id, created_at, updated_at, code, name, description)
SELECT
    'b0000000-0000-0000-0000-000000000011',
    now(),
    now(),
    'AGENT_EVENT_READ_ALL',
    'Read agent events across all tenants',
    'Allows viewing agent reports for every tenant, not only those the user is a member of'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'AGENT_EVENT_READ_ALL');

INSERT INTO role_permissions (id, created_at, updated_at, role_id, permission_id)
SELECT
    'c0000000-0000-0000-0000-000000000012',
    now(),
    now(),
    'a0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000011'
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions
    WHERE role_id = 'a0000000-0000-0000-0000-000000000001'
      AND permission_id = 'b0000000-0000-0000-0000-000000000011'
);
