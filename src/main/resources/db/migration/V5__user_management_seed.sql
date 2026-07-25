INSERT INTO permissions
(id, created_at, updated_at, code, name, description)
VALUES
    (
        'b0000000-0000-0000-0000-000000000004',
        now(),
        now(),
        'USER_READ',
        'Read users',
        'Allows viewing user records and their tenant memberships'
    ),
    (
        'b0000000-0000-0000-0000-000000000005',
        now(),
        now(),
        'USER_WRITE',
        'Write users',
        'Allows updating and soft-deleting user records'
    )
    ON CONFLICT (code) DO NOTHING;
INSERT INTO role_permissions
(id, created_at, updated_at, role_id, permission_id)
VALUES
    (
        'c0000000-0000-0000-0000-000000000004',
        now(),
        now(),
        'a0000000-0000-0000-0000-000000000001',
        'b0000000-0000-0000-0000-000000000004'
    ),
    (
        'c0000000-0000-0000-0000-000000000005',
        now(),
        now(),
        'a0000000-0000-0000-0000-000000000001',
        'b0000000-0000-0000-0000-000000000005'
    )
    ON CONFLICT DO NOTHING;