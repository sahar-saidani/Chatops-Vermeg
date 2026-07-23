create table tenants (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    code varchar(64) not null,
    name varchar(160) not null,
    active boolean not null,
    constraint uk_tenants_code unique (code)
);

create table users (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    email varchar(320) not null,
    normalized_email varchar(320) not null,
    display_name varchar(160) not null,
    password_hash varchar(255) not null,
    status varchar(32) not null,
    constraint uk_users_normalized_email unique (normalized_email),
    constraint ck_users_status check (status in ('PENDING_ACTIVATION', 'ACTIVE', 'LOCKED', 'DISABLED'))
);

create table roles (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    code varchar(100) not null,
    name varchar(120) not null,
    description varchar(500),
    constraint uk_roles_code unique (code)
);

create table permissions (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    code varchar(100) not null,
    name varchar(120) not null,
    description varchar(500),
    constraint uk_permissions_code unique (code)
);

create table role_permissions (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    role_id uuid not null,
    permission_id uuid not null,
    constraint fk_role_permissions_role foreign key (role_id) references roles (id),
    constraint fk_role_permissions_permission foreign key (permission_id) references permissions (id),
    constraint uk_role_permissions_role_permission unique (role_id, permission_id)
);

create table tenant_memberships (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    tenant_id uuid not null,
    user_id uuid not null,
    active boolean not null,
    constraint fk_tenant_memberships_tenant foreign key (tenant_id) references tenants (id),
    constraint fk_tenant_memberships_user foreign key (user_id) references users (id),
    constraint uk_tenant_memberships_tenant_user unique (tenant_id, user_id)
);

create table membership_roles (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    membership_id uuid not null,
    role_id uuid not null,
    constraint fk_membership_roles_membership foreign key (membership_id) references tenant_memberships (id),
    constraint fk_membership_roles_role foreign key (role_id) references roles (id),
    constraint uk_membership_roles_membership_role unique (membership_id, role_id)
);

create index ix_tenant_memberships_user_active on tenant_memberships (user_id, active);
create index ix_membership_roles_membership on membership_roles (membership_id);
create index ix_role_permissions_role on role_permissions (role_id);
