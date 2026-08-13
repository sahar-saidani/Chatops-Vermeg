package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.dto.PermissionMatrixResponse;
import com.vermeg.chatops.access.dto.RoleCreateRequest;
import com.vermeg.chatops.access.dto.RoleResponse;
import com.vermeg.chatops.access.dto.RoleUpdateRequest;

import java.util.List;
import java.util.UUID;

public interface RoleManagementService {

    List<RoleResponse> findAll();

    PermissionMatrixResponse findPermissionMatrix();

    RoleResponse findById(UUID id);

    RoleResponse create(RoleCreateRequest request);

    RoleResponse update(UUID id, RoleUpdateRequest request);

    void delete(UUID id);
}