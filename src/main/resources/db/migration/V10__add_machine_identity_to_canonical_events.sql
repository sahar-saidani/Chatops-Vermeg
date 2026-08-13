-- Every agent report now carries tenant/environment/environmentType/
-- machineReference (validated as required in DataProcessingAgentImpl), plus
-- optional nodeRole (CLUSTER environments) and jenkinsPurpose (jenkins-agent
-- only). Backfilling existing rows isn't possible (the data was never
-- captured), so the new required columns are added nullable and enforced
-- going forward at the application layer, consistent with how "environment"
-- itself already tolerates historical rows predating this feature.
-- One ALTER TABLE per column: PostgreSQL allows several comma-separated
-- ADD COLUMN clauses in a single statement, H2 (used by the test profile)
-- does not, and the combined form aborted the Flyway chain under `mvn test`.
ALTER TABLE canonical_events ADD COLUMN tenant VARCHAR(160);
ALTER TABLE canonical_events ADD COLUMN environment_type VARCHAR(20);
ALTER TABLE canonical_events ADD COLUMN machine_reference VARCHAR(255);
ALTER TABLE canonical_events ADD COLUMN node_role VARCHAR(20);
ALTER TABLE canonical_events ADD COLUMN jenkins_purpose VARCHAR(20);

CREATE INDEX ix_canonical_events_tenant ON canonical_events (tenant);
