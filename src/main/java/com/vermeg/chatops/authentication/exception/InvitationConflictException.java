package com.vermeg.chatops.authentication.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

public class InvitationConflictException extends ResponseStatusException {

    public InvitationConflictException(String email) {
        super(HttpStatus.CONFLICT, "An account already exists for '%s'".formatted(email));
    }
}
