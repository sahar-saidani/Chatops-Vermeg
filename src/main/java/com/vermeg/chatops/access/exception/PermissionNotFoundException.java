package com.vermeg.chatops.access.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

public class PermissionNotFoundException extends ResponseStatusException {

    public PermissionNotFoundException(UUID id) {
        super(HttpStatus.NOT_FOUND, "Permission '%s' was not found".formatted(id));
    }
}