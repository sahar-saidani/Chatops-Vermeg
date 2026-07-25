package com.vermeg.chatops.access.exception;

public class SystemRoleProtectedException extends RuntimeException {

    public SystemRoleProtectedException(String code) {
        super("System role '%s' cannot be deleted".formatted(code));
    }
}