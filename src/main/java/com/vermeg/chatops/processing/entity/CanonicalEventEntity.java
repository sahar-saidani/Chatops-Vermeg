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

    protected CanonicalEventEntity() {
    }

    public CanonicalEventEntity(CanonicalEvent event) {
        this.agentKey = event.agent();
        this.messageTimestamp = event.timestamp();
        this.environment = event.environment();
        this.data = event.data();
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
}