package com.vermeg.chatops.tenancy.service;

import com.vermeg.chatops.tenancy.dto.CreateTenantRequest;
import com.vermeg.chatops.tenancy.dto.TenantResponse;
import com.vermeg.chatops.tenancy.entity.TenantEntity;
import com.vermeg.chatops.tenancy.exception.TenantNameAlreadyExistsException;
import com.vermeg.chatops.tenancy.mapper.TenantMapper;
import com.vermeg.chatops.tenancy.repository.TenantRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class TenantManagementServiceImpl implements TenantManagementService {

    private final TenantRepository tenantRepository;
    private final TenantMapper tenantMapper;

    public TenantManagementServiceImpl(
            TenantRepository tenantRepository,
            TenantMapper tenantMapper
    ) {
        this.tenantRepository = tenantRepository;
        this.tenantMapper = tenantMapper;
    }

    @Override
    @Transactional
    public TenantResponse create(CreateTenantRequest request) {

        String tenantName = request.name().strip();

        if (tenantRepository.existsByNameIgnoreCase(tenantName)) {
            throw new TenantNameAlreadyExistsException(tenantName);
        }

        TenantEntity tenant = new TenantEntity(tenantName);

        tenant = tenantRepository.save(tenant);

        return tenantMapper.toResponse(tenant);
    }
}