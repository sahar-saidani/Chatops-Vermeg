package com.vermeg.chatops.tenancy.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;

import java.util.Locale;

@Entity
@Table(name = "tenants")
public class TenantEntity extends AuditableEntity {

    @Column(nullable = false, unique = true, length = 64)
    private String code;

    @Column(nullable = false, length = 160)
    private String name;

    @Column(nullable = false)
    private boolean active;

    protected TenantEntity() {
    }

    public TenantEntity(String code, String name) {
        this.code = normalizeCode(code);
        this.name = name.strip();
        this.active = true;
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public boolean isActive() {
        return active;
    }

    public void rename(String name) {
        this.name = name.strip();
    }

    public void deactivate() {
        this.active = false;
    }

    private static String normalizeCode(String value) {
        return value.strip().toUpperCase(Locale.ROOT);
    }
}
