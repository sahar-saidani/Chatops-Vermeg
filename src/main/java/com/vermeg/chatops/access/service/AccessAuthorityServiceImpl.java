package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.repository.TenantMembershipRepository;
import com.vermeg.chatops.identity.repository.UserRepository;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collection;
import java.util.List;
import java.util.Locale;

@Service
@Transactional(readOnly = true)
public class AccessAuthorityServiceImpl implements AccessAuthorityService {

    private final UserRepository userRepository;
    private final TenantMembershipRepository tenantMembershipRepository;

    public AccessAuthorityServiceImpl(
            UserRepository userRepository,
            TenantMembershipRepository tenantMembershipRepository
    ) {
        this.userRepository = userRepository;
        this.tenantMembershipRepository = tenantMembershipRepository;
    }

    @Override
    public boolean isActiveUser(String userEmail) {
        String normalizedEmail = userEmail.strip().toLowerCase(Locale.ROOT);
        return userRepository.findByNormalizedEmail(normalizedEmail)
                .map(user -> user.isActive())
                .orElse(false);
    }

    @Override
    public Collection<? extends GrantedAuthority> findAuthoritiesForActiveUser(String userEmail) {
        String normalizedEmail = userEmail.strip().toLowerCase(Locale.ROOT);
        if (!isActiveUser(normalizedEmail)) {
            return List.of();
        }
        return tenantMembershipRepository.findActivePermissionCodesByUserEmail(normalizedEmail).stream()
                .map(SimpleGrantedAuthority::new)
                .toList();
    }
}
