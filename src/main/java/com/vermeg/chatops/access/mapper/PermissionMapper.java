package com.vermeg.chatops.access.mapper;

import com.vermeg.chatops.access.dto.PermissionResponse;
import com.vermeg.chatops.access.entity.PermissionEntity;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface PermissionMapper {

    PermissionResponse toResponse(PermissionEntity permission);
}