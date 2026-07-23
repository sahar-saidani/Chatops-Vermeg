package com.vermeg.chatops.tenancy.controller;

import com.vermeg.chatops.tenancy.dto.CreateTenantRequest;
import com.vermeg.chatops.tenancy.dto.TenantResponse;
import com.vermeg.chatops.access.service.TenantAccessQueryService;
import com.vermeg.chatops.tenancy.service.TenantManagementService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/tenants")
public class TenantController {

    private final TenantManagementService tenantManagementService;
    private final TenantAccessQueryService tenantAccessQueryService;

    public TenantController(
            TenantManagementService tenantManagementService,
            TenantAccessQueryService tenantAccessQueryService
    ) {
        this.tenantManagementService = tenantManagementService;
        this.tenantAccessQueryService = tenantAccessQueryService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAuthority('TENANT_CREATE')")
    public TenantResponse create(@Valid @RequestBody CreateTenantRequest request) {
        return tenantManagementService.create(request);
    }

    @GetMapping
    public List<TenantResponse> findAssigned(Authentication authentication) {
        return tenantAccessQueryService.findAssignedTenants(authentication.getName());
    }
}
