package com.vermeg.chatops.access.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import com.vermeg.chatops.identity.entity.UserEntity;
import com.vermeg.chatops.tenancy.entity.TenantEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "tenant_memberships")
public class TenantMembershipEntity extends AuditableEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "tenant_id", nullable = false)
    private TenantEntity tenant;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private UserEntity user;

    @Column(nullable = false)
    private boolean active;

    protected TenantMembershipEntity() {
    }

    public TenantMembershipEntity(TenantEntity tenant, UserEntity user) {
        this.tenant = tenant;
        this.user = user;
        this.active = true;
    }

    public TenantEntity getTenant() {
        return tenant;
    }

    public UserEntity getUser() {
        return user;
    }

    public boolean isActive() {
        return active;
    }

    public void deactivate() {
        this.active = false;
    }
}
