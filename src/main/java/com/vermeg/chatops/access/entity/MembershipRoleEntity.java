package com.vermeg.chatops.access.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "membership_roles")
public class MembershipRoleEntity extends AuditableEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "membership_id", nullable = false)
    private TenantMembershipEntity membership;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "role_id", nullable = false)
    private RoleEntity role;

    protected MembershipRoleEntity() {
    }

    public MembershipRoleEntity(TenantMembershipEntity membership, RoleEntity role) {
        this.membership = membership;
        this.role = role;
    }

    public TenantMembershipEntity getMembership() {
        return membership;
    }

    public RoleEntity getRole() {
        return role;
    }
}
