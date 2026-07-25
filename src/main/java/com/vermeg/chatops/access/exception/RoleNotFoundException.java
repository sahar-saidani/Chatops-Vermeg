package com.vermeg.chatops.access.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

public class RoleNotFoundException extends ResponseStatusException {

    public RoleNotFoundException(UUID id) {
        super(HttpStatus.NOT_FOUND, "Role '%s' was not found".formatted(id));
    }
}