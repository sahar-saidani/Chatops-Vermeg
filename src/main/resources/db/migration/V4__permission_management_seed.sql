insert into permissions (id, created_at, updated_at, code, name, description) values
    ('b0000000-0000-0000-0000-000000000003', now(), now(), 'PERMISSION_MANAGE', 'Manage permissions', 'Allows creating and updating permissions');

insert into role_permissions (id, created_at, updated_at, role_id, permission_id) values
    ('c0000000-0000-0000-0000-000000000003', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000003');