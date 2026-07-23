package com.vermeg.chatops.access.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "role_permissions")
public class RolePermissionEntity extends AuditableEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "role_id", nullable = false)
    private RoleEntity role;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "permission_id", nullable = false)
    private PermissionEntity permission;

    protected RolePermissionEntity() {
    }

    public RolePermissionEntity(RoleEntity role, PermissionEntity permission) {
        this.role = role;
        this.permission = permission;
    }

    public RoleEntity getRole() {
        return role;
    }

    public PermissionEntity getPermission() {
        return permission;
    }
}
