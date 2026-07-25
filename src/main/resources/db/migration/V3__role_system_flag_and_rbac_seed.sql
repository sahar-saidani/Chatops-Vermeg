alter table roles add column is_system boolean not null default false;

insert into roles (id, created_at, updated_at, code, name, description, is_system) values
                                                                                       ('a0000000-0000-0000-0000-000000000001', now(), now(), 'ADMIN', 'Administrator', 'Full platform administrator with unrestricted access', true),
                                                                                       ('a0000000-0000-0000-0000-000000000002', now(), now(), 'TENANT_ADMIN', 'Tenant Administrator', 'Manages members and settings within an assigned tenant', true),
                                                                                       ('a0000000-0000-0000-0000-000000000003', now(), now(), 'USER', 'User', 'Standard platform user', true),
                                                                                       ('a0000000-0000-0000-0000-000000000004', now(), now(), 'OPERATOR', 'Operator', 'Operates agents and monitors executions', true);

insert into permissions (id, created_at, updated_at, code, name, description) values
                                                                                  ('b0000000-0000-0000-0000-000000000001', now(), now(), 'TENANT_CREATE', 'Create tenants', 'Allows creating new tenants'),
                                                                                  ('b0000000-0000-0000-0000-000000000002', now(), now(), 'ROLE_MANAGE', 'Manage roles', 'Allows creating, updating, and deleting roles');

insert into role_permissions (id, created_at, updated_at, role_id, permission_id) values
                                                                                      ('c0000000-0000-0000-0000-000000000001', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001'),
                                                                                      ('c0000000-0000-0000-0000-000000000002', now(), now(), 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002');