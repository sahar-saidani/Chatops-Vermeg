package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.dto.PermissionCreateRequest;
import com.vermeg.chatops.access.dto.PermissionResponse;
import com.vermeg.chatops.access.dto.PermissionUpdateRequest;

import java.util.List;
import java.util.UUID;

public interface PermissionManagementService {

    List<PermissionResponse> findAll();

    PermissionResponse findById(UUID id);

    PermissionResponse create(PermissionCreateRequest request);

    PermissionResponse update(UUID id, PermissionUpdateRequest request);
}