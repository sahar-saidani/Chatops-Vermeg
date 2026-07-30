package com.vermeg.chatops.identity.mapper;

import com.vermeg.chatops.access.entity.TenantMembershipEntity;
import com.vermeg.chatops.identity.dto.UserMembershipSummary;
import com.vermeg.chatops.identity.dto.UserResponse;
import com.vermeg.chatops.identity.entity.UserEntity;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface UserMapper {

    UserResponse toResponse(UserEntity user, List<UserMembershipSummary> memberships);

    @Mapping(target = "tenantId", source = "tenant.id")
    @Mapping(target = "tenantName", source = "tenant.name")
    UserMembershipSummary toMembershipSummary(TenantMembershipEntity membership);
}