package com.vermeg.chatops.tenancy.exception;

public class TenantCodeAlreadyExistsException extends RuntimeException {

    public TenantCodeAlreadyExistsException(String code) {
        super("A tenant with code '%s' already exists".formatted(code));
    }
}
