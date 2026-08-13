package com.vermeg.chatops.security.internal;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Authenticates trusted backend services (today: the Python LLM orchestrator)
 * by a shared secret header.
 *
 * <p>Why a key and not a service-account JWT: the orchestrator writes
 * conversation turns <em>on behalf of</em> whichever end user asked the
 * question, and it never holds that user's credentials. A service-account
 * login would still leave the row's owner coming from the request body, so the
 * JWT would add a login round-trip and a password to rotate without changing
 * the trust model. A single shared key states that model plainly: this caller
 * is a trusted process on the internal network, not a user.
 *
 * <p>The key is unset by default. With no key configured the filter
 * authenticates nobody, so the internal endpoints simply reject every caller
 * -- fail closed, never open.
 */
@Component
public class InternalServiceAuthenticationFilter extends OncePerRequestFilter {

    public static final String INTERNAL_SERVICE_AUTHORITY = "INTERNAL_SERVICE";
    private static final String HEADER = "X-Internal-Api-Key";
    private static final String PRINCIPAL = "internal-service";

    private final byte[] expectedKey;

    public InternalServiceAuthenticationFilter(@Value("${chatops.internal.api-key:}") String apiKey) {
        this.expectedKey = apiKey == null ? new byte[0] : apiKey.strip().getBytes(StandardCharsets.UTF_8);
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        if (expectedKey.length > 0 && SecurityContextHolder.getContext().getAuthentication() == null) {
            String presented = request.getHeader(HEADER);
            if (presented != null && matches(presented)) {
                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        PRINCIPAL,
                        null,
                        java.util.List.of(new SimpleGrantedAuthority(INTERNAL_SERVICE_AUTHORITY))
                );
                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        }
        filterChain.doFilter(request, response);
    }

    /** Constant-time so a wrong key cannot be recovered by timing the comparison. */
    private boolean matches(String presented) {
        return MessageDigest.isEqual(presented.strip().getBytes(StandardCharsets.UTF_8), expectedKey);
    }
}
