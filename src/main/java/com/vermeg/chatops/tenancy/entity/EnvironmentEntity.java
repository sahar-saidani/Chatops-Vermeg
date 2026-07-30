package com.vermeg.chatops.tenancy.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.util.Locale;
import java.util.Objects;

@Entity
@Table(
        name = "environments",
        uniqueConstraints = @UniqueConstraint(name = "uk_environment_tenant_name", columnNames = {"tenant_id", "name"})
)
public class EnvironmentEntity extends AuditableEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tenant_id", nullable = false, updatable = false)
    private TenantEntity tenant;

    @Column(nullable = false, length = 50)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private EnvironmentType type;

    protected EnvironmentEntity() {
    }

    /**
     * Package-private on purpose: an Environment is always created through
     * {@link TenantEntity#addEnvironment(String, EnvironmentType)} so the
     * tenant aggregate stays the single entry point, the same way
     * {@code TenantEntity}'s own constructor is the only way to get a valid
     * code/name pair.
     */
    EnvironmentEntity(TenantEntity tenant, String name, EnvironmentType type) {
        this.tenant = Objects.requireNonNull(tenant, "tenant must not be null");
        this.name = normalizeName(name);
        this.type = Objects.requireNonNull(type, "type must not be null");
    }

    public TenantEntity getTenant() {
        return tenant;
    }

    public String getName() {
        return name;
    }

    public EnvironmentType getType() {
        return type;
    }

    public void changeType(EnvironmentType type) {
        this.type = Objects.requireNonNull(type, "type must not be null");
    }

    private static String normalizeName(String value) {
        return value.strip().toUpperCase(Locale.ROOT);
    }
    public void rename(String name) {
        this.name = normalizeName(name);
    }
}