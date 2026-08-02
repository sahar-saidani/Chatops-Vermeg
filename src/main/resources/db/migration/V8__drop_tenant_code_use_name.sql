-- TenantEntity has never mapped the "code" column introduced in V1; every
-- tenant insert was failing on the NOT NULL constraint. The application
-- identifies tenants by name, so drop "code" and enforce uniqueness on
-- "name" at the database level instead of relying solely on the
-- existsByNameIgnoreCase() check in the service layer.
ALTER TABLE tenants DROP CONSTRAINT IF EXISTS uk_tenants_code;
ALTER TABLE tenants DROP COLUMN IF EXISTS code;
ALTER TABLE tenants ADD CONSTRAINT uk_tenants_name UNIQUE (name);
