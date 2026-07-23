package com.vermeg.chatops.audit.dto;

import com.vermeg.chatops.audit.entity.AuditEventType;

import java.time.Instant;
import java.util.UUID;

public final class AuditEventResponse {

    private final UUID id;
    private final AuditEventType eventType;
    private final String action;
    private final UUID subjectId;
    private final Instant occurredAt;

    public AuditEventResponse(
            UUID id,
            AuditEventType eventType,
            String action,
            UUID subjectId,
            Instant occurredAt
    ) {
        this.id = id;
        this.eventType = eventType;
        this.action = action;
        this.subjectId = subjectId;
        this.occurredAt = occurredAt;
    }

    public UUID getId() {
        return id;
    }

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
