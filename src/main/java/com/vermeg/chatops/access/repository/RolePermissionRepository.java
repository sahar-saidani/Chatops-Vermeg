package com.vermeg.chatops.access.repository;

import com.vermeg.chatops.access.entity.RolePermissionEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface RolePermissionRepository extends JpaRepository<RolePermissionEntity, UUID> {

    boolean existsByRole_IdAndPermission_Id(UUID roleId, UUID permissionId);

    List<RolePermissionEntity> findByRole_Id(UUID roleId);
}
