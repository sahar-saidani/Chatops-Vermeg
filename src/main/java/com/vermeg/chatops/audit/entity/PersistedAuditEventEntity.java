package com.vermeg.chatops.audit.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "audit_events")
public class PersistedAuditEventEntity extends AuditableEntity {

    @Enumerated(EnumType.STRING)
    @Column(name = "event_type", nullable = false, length = 64)
    private AuditEventType eventType;

    @Column(nullable = false, length = 128)
    private String action;

    @Column(name = "subject_id")
    private UUID subjectId;

    @Column(name = "occurred_at", nullable = false)
    private Instant occurredAt;

    @Column(nullable = false, columnDefinition = "text")
    private String details;

    protected PersistedAuditEventEntity() {
    }

    public PersistedAuditEventEntity(
            AuditEventType eventType,
            String action,
            UUID subjectId,
            Instant occurredAt,
            String details
    ) {
        this.eventType = eventType;
        this.action = action;
        this.subjectId = subjectId;
        this.occurredAt = occurredAt;
        this.details = details;
    }
}
