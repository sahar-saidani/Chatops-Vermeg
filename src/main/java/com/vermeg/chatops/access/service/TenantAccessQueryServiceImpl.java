package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.repository.TenantMembershipRepository;
import com.vermeg.chatops.tenancy.dto.TenantResponse;
import com.vermeg.chatops.tenancy.mapper.TenantMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;

@Service
@Transactional(readOnly = true)
public class TenantAccessQueryServiceImpl implements TenantAccessQueryService {

    private final TenantMembershipRepository tenantMembershipRepository;
    private final TenantMapper tenantMapper;

    public TenantAccessQueryServiceImpl(
            TenantMembershipRepository tenantMembershipRepository,
            TenantMapper tenantMapper
    ) {
        this.tenantMembershipRepository = tenantMembershipRepository;
        this.tenantMapper = tenantMapper;
    }

    @Override
    public List<TenantResponse> findAssignedTenants(String userEmail) {
        String normalizedEmail = userEmail.strip().toLowerCase(Locale.ROOT);
        return tenantMembershipRepository.findByUser_NormalizedEmailAndActiveTrueOrderByTenant_NameAsc(normalizedEmail)
                .stream()
                .filter(membership -> membership.getTenant().isActive())
                .map(membership -> tenantMapper.toResponse(membership.getTenant()))
                .toList();
    }
}
