-- EnvironmentController already requires ENVIRONMENT_CREATE/READ/UPDATE/DELETE
-- via @PreAuthorize, but none of these permissions were ever seeded, so no
-- role could be granted them and every Environment endpoint was unreachable.
insert into permissions (id, created_at, updated_at, code, name, description) values
    ('b0000000-0000-0000-0000-000000000006', now(), now(), 'ENVIRONMENT_CREATE', 'Create environments', 'Allows creating environments for a tenant'),
    ('b0000000-0000-0000-0000-000000000007', now(), now(), 'ENVIRONMENT_READ', 'Read environments', 'Allows viewing environments for a tenant'),
    ('b0000000-0000-0000-0000-000000000008', now(), now(), 'ENVIRONMENT_UPDATE', 'Update environments', 'Allows updating environments for a tenant'),
    ('b0000000-0000-0000-0000-000000000009', now(), now(), 'ENVIRONMENT_DELETE', 'Delete environments', 'Allows deleting environments for a tenant');

insert into role_permissions (id, created_at, updated_at, role_id, permission_id) values
    ('c0000000-0000-0000-0000-000000000006', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000006'),
    ('c0000000-0000-0000-0000-000000000007', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000007'),
    ('c0000000-0000-0000-0000-000000000008', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000008'),
    ('c0000000-0000-0000-0000-000000000009', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000009');
