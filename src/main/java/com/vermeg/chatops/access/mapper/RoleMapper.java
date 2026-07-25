package com.vermeg.chatops.access.mapper;

import com.vermeg.chatops.access.dto.RoleResponse;
import com.vermeg.chatops.access.entity.RoleEntity;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface RoleMapper {

    RoleResponse toResponse(RoleEntity role);
}