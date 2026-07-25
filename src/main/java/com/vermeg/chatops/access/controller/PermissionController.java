package com.vermeg.chatops.access.controller;

import com.vermeg.chatops.access.dto.PermissionCreateRequest;
import com.vermeg.chatops.access.dto.PermissionResponse;
import com.vermeg.chatops.access.dto.PermissionUpdateRequest;
import com.vermeg.chatops.access.service.PermissionManagementService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/permissions")
public class PermissionController {

    private final PermissionManagementService permissionManagementService;

    public PermissionController(PermissionManagementService permissionManagementService) {
        this.permissionManagementService = permissionManagementService;
    }

    @GetMapping
    @PreAuthorize("hasAuthority('PERMISSION_MANAGE')")
    public List<PermissionResponse> findAll() {
        return permissionManagementService.findAll();
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('PERMISSION_MANAGE')")
    public PermissionResponse findById(@PathVariable UUID id) {
        return permissionManagementService.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAuthority('PERMISSION_MANAGE')")
    public PermissionResponse create(@Valid @RequestBody PermissionCreateRequest request) {
        return permissionManagementService.create(request);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAuthority('PERMISSION_MANAGE')")
    public PermissionResponse update(@PathVariable UUID id, @Valid @RequestBody PermissionUpdateRequest request) {
        return permissionManagementService.update(id, request);
    }
}