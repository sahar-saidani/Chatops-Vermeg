package com.vermeg.chatops.identity.service;

import com.vermeg.chatops.identity.dto.UserResponse;
import com.vermeg.chatops.identity.dto.UserUpdateRequest;

import java.util.List;
import java.util.UUID;

public interface UserManagementService {

    List<UserResponse> findAll();

    UserResponse findById(UUID id);

    UserResponse update(UUID id, UserUpdateRequest request);

    void softDelete(UUID id);
}