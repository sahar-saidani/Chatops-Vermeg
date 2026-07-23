package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.repository.TenantMembershipRepository;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Locale;
import java.util.UUID;

@Service
@Transactional(readOnly = true)
public class TenantPermissionAuthorizationServiceImpl implements TenantPermissionAuthorizationService {

    private final TenantMembershipRepository tenantMembershipRepository;

    public TenantPermissionAuthorizationServiceImpl(TenantMembershipRepository tenantMembershipRepository) {
        this.tenantMembershipRepository = tenantMembershipRepository;
    }

    @Override
    public void requirePermission(String userEmail, UUID tenantId, String permissionCode) {
        String normalizedEmail = userEmail.strip().toLowerCase(Locale.ROOT);
        boolean permitted = tenantMembershipRepository
                .findActivePermissionCodesByUserEmailAndTenantId(normalizedEmail, tenantId)
                .contains(permissionCode);
        if (!permitted) {
            throw new AccessDeniedException("The authenticated user is not authorized for this tenant operation");
        }
    }
}
