package com.vermeg.chatops.tenancy.exception;

public class TenantNameAlreadyExistsException extends RuntimeException {

    public TenantNameAlreadyExistsException(String name) {
        super("A tenant with name '" + name + "' already exists.");
    }
}