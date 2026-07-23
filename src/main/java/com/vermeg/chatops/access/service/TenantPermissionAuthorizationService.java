package com.vermeg.chatops.access.service;

import org.springframework.security.access.AccessDeniedException;

import java.util.UUID;

public interface TenantPermissionAuthorizationService {

    void requirePermission(String userEmail, UUID tenantId, String permissionCode) throws AccessDeniedException;
}
