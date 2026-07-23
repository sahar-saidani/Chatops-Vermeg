package com.vermeg.chatops.authentication.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

public class InvalidTokenException extends ResponseStatusException {

    public InvalidTokenException(String message) {
        super(HttpStatus.BAD_REQUEST, message);
    }
}
