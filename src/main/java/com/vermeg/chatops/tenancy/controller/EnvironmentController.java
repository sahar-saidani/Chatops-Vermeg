package com.vermeg.chatops.tenancy.controller;

import com.vermeg.chatops.tenancy.dto.CreateEnvironmentRequest;
import com.vermeg.chatops.tenancy.dto.EnvironmentResponse;
import com.vermeg.chatops.tenancy.dto.UpdateEnvironmentRequest;
import com.vermeg.chatops.tenancy.service.EnvironmentManagementService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
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
@RequestMapping("/api/v1/tenants/{tenantId}/environments")
public class EnvironmentController {

    private final EnvironmentManagementService environmentManagementService;

    public EnvironmentController(EnvironmentManagementService environmentManagementService) {
        this.environmentManagementService = environmentManagementService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAuthority('ENVIRONMENT_CREATE')")
    public EnvironmentResponse create(
            @PathVariable UUID tenantId,
            @Valid @RequestBody CreateEnvironmentRequest request
    ) {
        return environmentManagementService.create(tenantId, request);
    }

    @GetMapping
    @PreAuthorize("hasAuthority('ENVIRONMENT_READ')")
    public List<EnvironmentResponse> findAll(@PathVariable UUID tenantId) {
        return environmentManagementService.findAllForTenant(tenantId);
    }

    @GetMapping("/{environmentId}")
    @PreAuthorize("hasAuthority('ENVIRONMENT_READ')")
    public EnvironmentResponse findOne(
            @PathVariable UUID tenantId,
            @PathVariable UUID environmentId
    ) {
        return environmentManagementService.findOne(tenantId, environmentId);
    }

    @PutMapping("/{environmentId}")
    @PreAuthorize("hasAuthority('ENVIRONMENT_UPDATE')")
    public EnvironmentResponse update(
            @PathVariable UUID tenantId,
            @PathVariable UUID environmentId,
            @Valid @RequestBody UpdateEnvironmentRequest request
    ) {
        return environmentManagementService.update(tenantId, environmentId, request);
    }

    @DeleteMapping("/{environmentId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasAuthority('ENVIRONMENT_DELETE')")
    public void delete(
            @PathVariable UUID tenantId,
            @PathVariable UUID environmentId
    ) {
        environmentManagementService.delete(tenantId, environmentId);
    }
}
