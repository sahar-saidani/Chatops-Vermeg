package com.vermeg.chatops.authentication.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import com.vermeg.chatops.identity.entity.UserEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "authentication_tokens")
public class AuthenticationTokenEntity extends AuditableEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private UserEntity user;

    @Column(name = "token_hash", nullable = false, unique = true, length = 64)
    private String tokenHash;

    @Enumerated(EnumType.STRING)
    @Column(name = "token_type", nullable = false, length = 32)
    private AuthenticationTokenType tokenType;

    @Column(name = "family_id")
    private UUID familyId;

    @Column(name = "expires_at", nullable = false)
    private Instant expiresAt;

    @Column(name = "used_at")
    private Instant usedAt;

    @Column(name = "revoked_at")
    private Instant revokedAt;

    protected AuthenticationTokenEntity() {
    }

    public AuthenticationTokenEntity(
            UserEntity user,
            String tokenHash,
            AuthenticationTokenType tokenType,
            UUID familyId,
            Instant expiresAt
    ) {
        this.user = user;
        this.tokenHash = tokenHash;
        this.tokenType = tokenType;
        this.familyId = familyId;
        this.expiresAt = expiresAt;
    }

    public UserEntity getUser() {
        return user;
    }

    public AuthenticationTokenType getTokenType() {
        return tokenType;
    }

    public UUID getFamilyId() {
        return familyId;
    }

    public boolean isUsableAt(Instant instant) {
        return usedAt == null && revokedAt == null && expiresAt.isAfter(instant);
    }

    public void markUsed(Instant instant) {
        this.usedAt = instant;
    }

    public void revoke(Instant instant) {
        if (revokedAt == null) {
            this.revokedAt = instant;
        }
    }
}
