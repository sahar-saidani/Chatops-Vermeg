package com.vermeg.chatops.audit.service;

import com.vermeg.chatops.audit.dto.AuditEventRequest;

/** Application port for recording cross-cutting audit events. */
public interface AuditService {

    void record(AuditEventRequest event);
}
