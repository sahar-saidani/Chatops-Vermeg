package com.vermeg.chatops.access.exception;

public class RoleCodeAlreadyExistsException extends RuntimeException {
    public RoleCodeAlreadyExistsException(String message) {
        super(message);
    }
}
