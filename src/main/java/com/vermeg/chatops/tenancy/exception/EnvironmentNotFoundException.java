package com.vermeg.chatops.tenancy.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

import java.util.UUID;

@ResponseStatus(HttpStatus.NOT_FOUND)
public class EnvironmentNotFoundException extends RuntimeException {

    public EnvironmentNotFoundException(UUID tenantId, UUID environmentId) {
        super("Environment " + environmentId + " not found for tenant " + tenantId);
    }
}
