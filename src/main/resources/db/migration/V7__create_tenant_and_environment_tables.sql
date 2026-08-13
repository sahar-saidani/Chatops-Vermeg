-- "DEFAULT ... PRIMARY KEY" rather than "PRIMARY KEY DEFAULT ...": PostgreSQL
-- accepts either order, H2 (used by the test profile) only the former, and the
-- reversed order aborted the whole Flyway chain before any Spring context
-- could load under `mvn test`.
CREATE TABLE environments (
                              id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                              tenant_id  UUID NOT NULL,
                              name       VARCHAR(50) NOT NULL,
                              type       VARCHAR(20) NOT NULL,
                              created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                              updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                              created_by VARCHAR(255),
                              updated_by VARCHAR(255),
                              CONSTRAINT fk_environment_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
                              CONSTRAINT uk_environment_tenant_name UNIQUE (tenant_id, name),
                              CONSTRAINT chk_environment_type CHECK (type IN ('STANDALONE', 'CLUSTER'))
);

CREATE INDEX idx_environment_tenant_id ON environments (tenant_id);