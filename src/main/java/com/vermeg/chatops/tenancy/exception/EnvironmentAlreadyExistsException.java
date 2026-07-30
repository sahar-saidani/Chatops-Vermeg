package com.vermeg.chatops.tenancy.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

import java.util.UUID;

@ResponseStatus(HttpStatus.CONFLICT)
public class EnvironmentAlreadyExistsException extends RuntimeException {

    public EnvironmentAlreadyExistsException(UUID tenantId, String name) {
        super("Environment '" + name + "' already exists for tenant " + tenantId);
    }
}
