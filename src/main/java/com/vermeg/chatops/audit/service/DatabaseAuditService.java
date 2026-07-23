package com.vermeg.chatops.audit.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vermeg.chatops.audit.dto.AuditEventRequest;
import com.vermeg.chatops.audit.entity.PersistedAuditEventEntity;
import com.vermeg.chatops.audit.repository.PersistedAuditEventRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DatabaseAuditService implements AuditService {

    private final PersistedAuditEventRepository auditEventRepository;
    private final ObjectMapper objectMapper;

    public DatabaseAuditService(PersistedAuditEventRepository auditEventRepository, ObjectMapper objectMapper) {
        this.auditEventRepository = auditEventRepository;
        this.objectMapper = objectMapper;
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void record(AuditEventRequest event) {
        auditEventRepository.save(new PersistedAuditEventEntity(
                event.getEventType(),
                event.getAction(),
                event.getSubjectId(),
                event.getOccurredAt(),
                serializeDetails(event)
        ));
    }

    private String serializeDetails(AuditEventRequest event) {
        try {
            return objectMapper.writeValueAsString(event.getDetails());
        } catch (JsonProcessingException exception) {
            throw new IllegalArgumentException("Audit event details cannot be serialized", exception);
        }
    }
}
