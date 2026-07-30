package com.vermeg.chatops.tenancy.service;

import com.vermeg.chatops.tenancy.dto.CreateEnvironmentRequest;
import com.vermeg.chatops.tenancy.dto.EnvironmentResponse;
import com.vermeg.chatops.tenancy.dto.UpdateEnvironmentRequest;
import com.vermeg.chatops.tenancy.entity.EnvironmentEntity;
import com.vermeg.chatops.tenancy.entity.TenantEntity;
import com.vermeg.chatops.tenancy.exception.EnvironmentAlreadyExistsException;
import com.vermeg.chatops.tenancy.exception.EnvironmentNotFoundException;
import com.vermeg.chatops.tenancy.exception.TenantNotFoundException;
import com.vermeg.chatops.tenancy.mapper.EnvironmentMapper;
import com.vermeg.chatops.tenancy.repository.EnvironmentRepository;
import com.vermeg.chatops.tenancy.repository.TenantRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/**
 * CRUD for Environment, always scoped to its owning Tenant - there is no
 * "find environment by id alone" path, mirroring the aggregate boundary
 * expressed by TenantEntity.addEnvironment(...).
 *
 * Deliberately out of scope here: EnvironmentVariable CRUD.
 */
@Service
public class EnvironmentManagementService {

    private final EnvironmentRepository environmentRepository;
    private final TenantRepository tenantRepository;

    public EnvironmentManagementService(
            EnvironmentRepository environmentRepository,
            TenantRepository tenantRepository
    ) {
        this.environmentRepository = environmentRepository;
        this.tenantRepository = tenantRepository;
    }

    @Transactional
    public EnvironmentResponse create(UUID tenantId, CreateEnvironmentRequest request) {
        TenantEntity tenant = getTenant(tenantId);
        assertNameAvailable(tenantId, request.name());

        EnvironmentEntity environment = tenant.addEnvironment(request.name(), request.type());
        tenantRepository.save(tenant); // cascades to the new EnvironmentEntity (CascadeType.ALL)

        return EnvironmentMapper.toResponse(environment);
    }

    @Transactional(readOnly = true)
    public List<EnvironmentResponse> findAllForTenant(UUID tenantId) {
        assertTenantExists(tenantId);
        return environmentRepository.findAllByTenantId(tenantId).stream()
                .map(EnvironmentMapper::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public EnvironmentResponse findOne(UUID tenantId, UUID environmentId) {
        return EnvironmentMapper.toResponse(getOwnedEnvironment(tenantId, environmentId));
    }

    @Transactional
    public EnvironmentResponse update(UUID tenantId, UUID environmentId, UpdateEnvironmentRequest request) {
        EnvironmentEntity environment = getOwnedEnvironment(tenantId, environmentId);

        if (!environment.getName().equalsIgnoreCase(request.name())) {
            assertNameAvailable(tenantId, request.name());
        }

        environment.rename(request.name());
        environment.changeType(request.type());

        return EnvironmentMapper.toResponse(environment);
    }

    @Transactional
    public void delete(UUID tenantId, UUID environmentId) {
        EnvironmentEntity environment = getOwnedEnvironment(tenantId, environmentId);
        environmentRepository.delete(environment);
    }

    private EnvironmentEntity getOwnedEnvironment(UUID tenantId, UUID environmentId) {
        return environmentRepository.findByIdAndTenantId(environmentId, tenantId)
                .orElseThrow(() -> new EnvironmentNotFoundException(tenantId, environmentId));
    }

    private TenantEntity getTenant(UUID tenantId) {
        return tenantRepository.findById(tenantId)
                .orElseThrow(() -> new TenantNotFoundException(tenantId));
    }

    private void assertTenantExists(UUID tenantId) {
        if (!tenantRepository.existsById(tenantId)) {
            throw new TenantNotFoundException(tenantId);
        }
    }

    private void assertNameAvailable(UUID tenantId, String name) {
        if (environmentRepository.existsByTenantIdAndNameIgnoreCase(tenantId, name)) {
            throw new EnvironmentAlreadyExistsException(tenantId, name);
        }
    }
}
