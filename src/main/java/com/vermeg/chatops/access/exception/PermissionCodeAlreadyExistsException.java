package com.vermeg.chatops.access.exception;

public class PermissionCodeAlreadyExistsException extends RuntimeException {

    public PermissionCodeAlreadyExistsException(String code) {
        super("A permission with code '%s' already exists".formatted(code));
    }
}