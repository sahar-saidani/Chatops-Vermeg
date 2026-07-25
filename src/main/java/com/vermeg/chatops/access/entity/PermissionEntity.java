package com.vermeg.chatops.access.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;

import java.util.Locale;

@Entity
@Table(name = "permissions")
public class PermissionEntity extends AuditableEntity {

    @Column(nullable = false, unique = true, length = 100)
    private String code;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(length = 500)
    private String description;

    protected PermissionEntity() {
    }

    public PermissionEntity(String code, String name, String description) {
        this.code = normalizeCode(code);
        this.name = name.strip();
        this.description = normalizeDescription(description);
    }
    public void updateDetails(String name, String description) {
        this.name = name.strip();
        this.description = normalizeDescription(description);
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    private static String normalizeCode(String value) {
        return value.strip().toUpperCase(Locale.ROOT);
    }

    private static String normalizeDescription(String value) {
        return value == null || value.isBlank() ? null : value.strip();
    }
}
