package com.vermeg.chatops.audit.repository;

import com.vermeg.chatops.audit.entity.PersistedAuditEventEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface PersistedAuditEventRepository extends JpaRepository<PersistedAuditEventEntity, UUID> {
}
