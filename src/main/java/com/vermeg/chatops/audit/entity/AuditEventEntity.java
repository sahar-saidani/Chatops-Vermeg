package com.vermeg.chatops.audit.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.MappedSuperclass;

import java.time.Instant;
import java.util.UUID;

/**
 * Persistence blueprint for concrete audit records introduced by a later migration.
 */
@MappedSuperclass
public abstract class AuditEventEntity extends AuditableEntity {

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 64)
    private AuditEventType eventType;

    @Column(nullable = false, length = 128)
    private String action;

    private UUID subjectId;

    @Column(nullable = false)
    private Instant occurredAt;

    public AuditEventType getEventType() {
        return eventType;
    }

    public String getAction() {
        return action;
    }

    public UUID getSubjectId() {
        return subjectId;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}
