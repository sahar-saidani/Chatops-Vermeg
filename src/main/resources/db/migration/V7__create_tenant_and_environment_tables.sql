-- Rename this file to V<next available number>__create_environments_table.sql
-- (check src/main/resources/db/migration/ for the current highest Vn first)

CREATE TABLE environments (
                              id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                              tenant_id  UUID NOT NULL,
                              name       VARCHAR(50) NOT NULL,
                              type       VARCHAR(20) NOT NULL,
                              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                              updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                              created_by VARCHAR(255),
                              updated_by VARCHAR(255),
                              CONSTRAINT fk_environment_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
                              CONSTRAINT uk_environment_tenant_name UNIQUE (tenant_id, name),
                              CONSTRAINT chk_environment_type CHECK (type IN ('STANDALONE', 'CLUSTER'))
);

CREATE INDEX idx_environment_tenant_id ON environments (tenant_id);