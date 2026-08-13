-- Idempotent seed for the USER_READ / USER_WRITE permissions used by
-- UserController's @PreAuthorize checks.
--
-- This originally used PostgreSQL's "ON CONFLICT ... DO NOTHING", which H2
-- does not implement in any compatibility mode, so the whole Flyway chain
-- aborted on the test profile (application-test.yml runs H2) and no Spring
-- context could ever load. The guarded "INSERT ... SELECT ... WHERE NOT
-- EXISTS" form below is standard SQL, keeps the same "insert only if absent"
-- semantics, and runs identically on PostgreSQL and H2.
INSERT INTO permissions (id, created_at, updated_at, code, name, description)
SELECT
    'b0000000-0000-0000-0000-000000000004',
    now(),
    now(),
    'USER_READ',
    'Read users',
    'Allows viewing user records and their tenant memberships'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'USER_READ');

INSERT INTO permissions (id, created_at, updated_at, code, name, description)
SELECT
    'b0000000-0000-0000-0000-000000000005',
    now(),
    now(),
    'USER_WRITE',
    'Write users',
    'Allows updating and soft-deleting user records'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'USER_WRITE');

INSERT INTO role_permissions (id, created_at, updated_at, role_id, permission_id)
SELECT
    'c0000000-0000-0000-0000-000000000004',
    now(),
    now(),
    'a0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000004'
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions
    WHERE role_id = 'a0000000-0000-0000-0000-000000000001'
      AND permission_id = 'b0000000-0000-0000-0000-000000000004'
);

INSERT INTO role_permissions (id, created_at, updated_at, role_id, permission_id)
SELECT
    'c0000000-0000-0000-0000-000000000005',
    now(),
    now(),
    'a0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000005'
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions
    WHERE role_id = 'a0000000-0000-0000-0000-000000000001'
      AND permission_id = 'b0000000-0000-0000-0000-000000000005'
);
