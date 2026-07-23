package com.vermeg.chatops.audit.dto;

import com.vermeg.chatops.audit.entity.AuditEventType;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public final class AuditEventRequest {

    private final AuditEventType eventType;
    private final String action;
    private final UUID subjectId;
    private final Instant occurredAt;
    private final Map<String, Object> details;

    public AuditEventRequest(
            AuditEventType eventType,
            String action,
            UUID subjectId,
            Instant occurredAt,
            Map<String, Object> details
    ) {
        this.eventType = eventType;
        this.action = action;
        this.subjectId = subjectId;
        this.occurredAt = occurredAt;
        this.details = Map.copyOf(details);
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

    public Map<String, Object> getDetails() {
        return details;
    }
}
