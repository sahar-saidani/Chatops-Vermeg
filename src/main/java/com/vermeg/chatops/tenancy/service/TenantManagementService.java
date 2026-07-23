package com.vermeg.chatops.tenancy.service;

import com.vermeg.chatops.tenancy.dto.CreateTenantRequest;
import com.vermeg.chatops.tenancy.dto.TenantResponse;

public interface TenantManagementService {

    TenantResponse create(CreateTenantRequest request);
}
