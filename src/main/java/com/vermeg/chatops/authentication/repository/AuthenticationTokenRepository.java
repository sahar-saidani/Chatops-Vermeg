package com.vermeg.chatops.authentication.repository;

import com.vermeg.chatops.authentication.entity.AuthenticationTokenEntity;
import com.vermeg.chatops.authentication.entity.AuthenticationTokenType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.Lock;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

public interface AuthenticationTokenRepository extends JpaRepository<AuthenticationTokenEntity, UUID> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    Optional<AuthenticationTokenEntity> findByTokenHashAndTokenType(String tokenHash, AuthenticationTokenType tokenType);

    @Modifying
    @Query("""
            update AuthenticationTokenEntity token
            set token.revokedAt = :revokedAt
            where token.user.id = :userId
              and token.tokenType = :tokenType
              and token.revokedAt is null
              and token.usedAt is null
            """)
    int revokeUnusedTokensForUser(
            @Param("userId") UUID userId,
            @Param("tokenType") AuthenticationTokenType tokenType,
            @Param("revokedAt") Instant revokedAt
    );
}
