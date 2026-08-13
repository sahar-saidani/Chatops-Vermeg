-- Permission for reading agent reports out of canonical_events.
--
-- Granted to ADMIN and OPERATOR: OPERATOR is described in V3 as the role that
-- "operates agents and monitors executions", which is exactly this endpoint.
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
