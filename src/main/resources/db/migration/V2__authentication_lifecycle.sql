create table authentication_tokens (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    user_id uuid not null,
    token_hash varchar(64) not null,
    token_type varchar(32) not null,
    family_id uuid,
    expires_at timestamp with time zone not null,
    used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    constraint fk_authentication_tokens_user foreign key (user_id) references users (id),
    constraint uk_authentication_tokens_hash unique (token_hash),
    constraint ck_authentication_tokens_type check (token_type in ('REFRESH', 'INVITATION', 'PASSWORD_RESET'))
);

create index ix_authentication_tokens_user_type on authentication_tokens (user_id, token_type);
create index ix_authentication_tokens_expiration on authentication_tokens (expires_at);

create table audit_events (
    id uuid primary key,
    created_at timestamp with time zone not null,
    updated_at timestamp with time zone not null,
    created_by varchar(255),
    updated_by varchar(255),
    event_type varchar(64) not null,
    action varchar(128) not null,
    subject_id uuid,
    occurred_at timestamp with time zone not null,
    details text not null
);

create index ix_audit_events_subject_occurred on audit_events (subject_id, occurred_at);
create index ix_audit_events_type_occurred on audit_events (event_type, occurred_at);
