package com.vermeg.chatops.tenancy.mapper;

import com.vermeg.chatops.tenancy.dto.EnvironmentResponse;
import com.vermeg.chatops.tenancy.dto.TenantSummaryResponse;
import com.vermeg.chatops.tenancy.entity.EnvironmentEntity;
import com.vermeg.chatops.tenancy.entity.TenantEntity;

public final class EnvironmentMapper {

    private EnvironmentMapper() {
    }

    public static EnvironmentResponse toResponse(EnvironmentEntity entity) {
        return new EnvironmentResponse(
                entity.getId(),
                entity.getName(),
                entity.getType(),
                toTenantSummary(entity.getTenant()),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    public static TenantSummaryResponse toTenantSummary(TenantEntity tenant) {
        return new TenantSummaryResponse(tenant.getId() , tenant.getName());
    }
}
