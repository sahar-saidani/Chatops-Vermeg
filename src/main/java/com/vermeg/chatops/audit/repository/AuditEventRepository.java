package com.vermeg.chatops.audit.repository;

import com.vermeg.chatops.audit.entity.AuditEventEntity;

/** Port to be implemented when a concrete audit record and its migration are introduced. */
public interface AuditEventRepository {

    <T extends AuditEventEntity> T save(T auditEvent);
}
