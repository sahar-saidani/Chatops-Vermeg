package com.vermeg.chatops.processing.entity;

import com.vermeg.chatops.common.events.CanonicalEvent;
import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.Map;

@Entity
@Table(name = "canonical_events")
public class CanonicalEventEntity extends AuditableEntity {

    @Column(name = "agent_key", nullable = false, length = 64)
    private String agentKey;

    @Column(name = "message_timestamp", nullable = false)
    private Instant messageTimestamp;

    @Column(nullable = false, length = 32)
    private String environment;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> data;

    @Column(length = 160)
    private String tenant;

    @Column(name = "environment_type", length = 20)
    private String environmentType;

    @Column(name = "machine_reference", length = 255)
    private String machineReference;

    @Column(name = "node_role", length = 20)
    private String nodeRole;

    @Column(name = "jenkins_purpose", length = 20)
    private String jenkinsPurpose;

    protected CanonicalEventEntity() {
    }

    public CanonicalEventEntity(CanonicalEvent event) {
        this.agentKey = event.agent();
        this.messageTimestamp = event.timestamp();
        this.environment = event.environment();
        this.data = event.data();
        this.tenant = event.tenant();
        this.environmentType = event.environmentType();
        this.machineReference = event.machineReference();
        this.nodeRole = event.nodeRole();
        this.jenkinsPurpose = event.jenkinsPurpose();
    }

    public String getAgentKey() {
        return agentKey;
    }

    public Instant getMessageTimestamp() {
        return messageTimestamp;
    }

    public String getEnvironment() {
        return environment;
    }

    public Map<String, Object> getData() {
        return data;
    }

    public String getTenant() {
        return tenant;
    }

    public String getEnvironmentType() {
        return environmentType;
    }

    public String getMachineReference() {
        return machineReference;
    }

    public String getNodeRole() {
        return nodeRole;
    }

    public String getJenkinsPurpose() {
        return jenkinsPurpose;
    }
}