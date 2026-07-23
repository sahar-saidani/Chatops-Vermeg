package com.vermeg.chatops.identity.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;

import java.util.Locale;

@Entity
@Table(name = "users")
public class UserEntity extends AuditableEntity {

    @Column(nullable = false, length = 320)
    private String email;

    @Column(name = "normalized_email", nullable = false, unique = true, length = 320)
    private String normalizedEmail;

    @Column(name = "display_name", nullable = false, length = 160)
    private String displayName;

    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private UserStatus status;

    protected UserEntity() {
    }

    public UserEntity(String email, String displayName, String passwordHash) {
        this.email = normalizeEmail(email);
        this.normalizedEmail = normalizeEmail(email);
        this.displayName = displayName.strip();
        this.passwordHash = passwordHash;
        this.status = UserStatus.PENDING_ACTIVATION;
    }

    public String getEmail() {
        return email;
    }

    public String getNormalizedEmail() {
        return normalizedEmail;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public UserStatus getStatus() {
        return status;
    }

    public boolean isActive() {
        return status == UserStatus.ACTIVE;
    }

    public void activate() {
        this.status = UserStatus.ACTIVE;
    }

    public void lock() {
        this.status = UserStatus.LOCKED;
    }

    public void disable() {
        this.status = UserStatus.DISABLED;
    }

    public void changePassword(String passwordHash) {
        this.passwordHash = passwordHash;
    }

    private static String normalizeEmail(String value) {
        return value.strip().toLowerCase(Locale.ROOT);
    }
}
