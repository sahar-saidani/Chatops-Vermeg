package com.vermeg.chatops.access.service;

import com.vermeg.chatops.tenancy.dto.TenantResponse;

import java.util.List;

public interface TenantAccessQueryService {

    List<TenantResponse> findAssignedTenants(String userEmail);
}
