package com.vermeg.chatops.tenancy.mapper;

import com.vermeg.chatops.tenancy.dto.TenantResponse;
import com.vermeg.chatops.tenancy.entity.TenantEntity;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface TenantMapper {

    TenantResponse toResponse(TenantEntity tenant);
}
