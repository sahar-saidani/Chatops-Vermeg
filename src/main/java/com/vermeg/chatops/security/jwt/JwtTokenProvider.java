package com.vermeg.chatops.security.jwt;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Optional;

@Component
public class JwtTokenProvider {

    private final String secret;
    private final long expirationMillis;

    public JwtTokenProvider(
            @Value("${security.jwt.secret:}") String secret,
            @Value("${security.jwt.expiration:3600000}") long expirationMillis
    ) {
        this.secret = secret;
        this.expirationMillis = expirationMillis;
    }

    public String generateToken(String subject) {
        Instant issuedAt = Instant.now();
        return Jwts.builder()
                .subject(subject)
                .issuedAt(Date.from(issuedAt))
                .expiration(Date.from(issuedAt.plusMillis(expirationMillis)))
                .signWith(signingKey())
                .compact();
    }

    public Optional<String> getSubject(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(signingKey())
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            return Optional.ofNullable(claims.getSubject());
        } catch (JwtException | IllegalArgumentException exception) {
            return Optional.empty();
        }
    }

    public boolean isValid(String token) {
        return getSubject(token).isPresent();
    }

    private SecretKey signingKey() {
        if (secret.isBlank()) {
            throw new IllegalStateException("JWT_SECRET must be configured before issuing or validating tokens");
        }
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
}
