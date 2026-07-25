package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.dto.PermissionCreateRequest;
import com.vermeg.chatops.access.dto.PermissionResponse;
import com.vermeg.chatops.access.dto.PermissionUpdateRequest;
import com.vermeg.chatops.access.entity.PermissionEntity;
import com.vermeg.chatops.access.exception.PermissionCodeAlreadyExistsException;
import com.vermeg.chatops.access.exception.PermissionNotFoundException;
import com.vermeg.chatops.access.mapper.PermissionMapper;
import com.vermeg.chatops.access.repository.PermissionRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
@Transactional(readOnly = true)
public class PermissionManagementServiceImpl implements PermissionManagementService {

    private final PermissionRepository permissionRepository;
    private final PermissionMapper permissionMapper;

    public PermissionManagementServiceImpl(
            PermissionRepository permissionRepository,
            PermissionMapper permissionMapper
    ) {
        this.permissionRepository = permissionRepository;
        this.permissionMapper = permissionMapper;
    }

    @Override
    public List<PermissionResponse> findAll() {
        return permissionRepository.findAll(Sort.by(Sort.Direction.ASC, "name")).stream()
                .map(permissionMapper::toResponse)
                .toList();
    }

    @Override
    public PermissionResponse findById(UUID id) {
        return permissionMapper.toResponse(getPermissionOrThrow(id));
    }

    @Override
    @Transactional
    public PermissionResponse create(PermissionCreateRequest request) {
        String normalizedCode = request.code().strip().toUpperCase(Locale.ROOT);
        if (permissionRepository.findByCode(normalizedCode).isPresent()) {
            throw new PermissionCodeAlreadyExistsException(normalizedCode);
        }
        PermissionEntity permission = permissionRepository.save(
                new PermissionEntity(normalizedCode, request.name(), request.description())
        );
        return permissionMapper.toResponse(permission);
    }

    @Override
    @Transactional
    public PermissionResponse update(UUID id, PermissionUpdateRequest request) {
        PermissionEntity permission = getPermissionOrThrow(id);
        permission.updateDetails(request.name(), request.description());
        return permissionMapper.toResponse(permission);
    }

    private PermissionEntity getPermissionOrThrow(UUID id) {
        return permissionRepository.findById(id).orElseThrow(() -> new PermissionNotFoundException(id));
    }
}