-- Every agent report now carries tenant/environment/environmentType/
-- machineReference (validated as required in DataProcessingAgentImpl), plus
-- optional nodeRole (CLUSTER environments) and jenkinsPurpose (jenkins-agent
-- only). Backfilling existing rows isn't possible (the data was never
-- captured), so the new required columns are added nullable and enforced
-- going forward at the application layer, consistent with how "environment"
-- itself already tolerates historical rows predating this feature.
ALTER TABLE canonical_events
    ADD COLUMN tenant VARCHAR(160),
    ADD COLUMN environment_type VARCHAR(20),
    ADD COLUMN machine_reference VARCHAR(255),
    ADD COLUMN node_role VARCHAR(20),
    ADD COLUMN jenkins_purpose VARCHAR(20);

CREATE INDEX ix_canonical_events_tenant ON canonical_events (tenant);
