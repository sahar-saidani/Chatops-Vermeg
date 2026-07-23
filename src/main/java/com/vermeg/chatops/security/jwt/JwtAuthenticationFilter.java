package com.vermeg.chatops.security.jwt;

import com.vermeg.chatops.access.service.AccessAuthorityService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtTokenProvider jwtTokenProvider;
    private final AccessAuthorityService accessAuthorityService;

    public JwtAuthenticationFilter(
            JwtTokenProvider jwtTokenProvider,
            AccessAuthorityService accessAuthorityService
    ) {
        this.jwtTokenProvider = jwtTokenProvider;
        this.accessAuthorityService = accessAuthorityService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        String authorization = request.getHeader("Authorization");
        if (authorization != null && authorization.startsWith(BEARER_PREFIX)
                && SecurityContextHolder.getContext().getAuthentication() == null) {
            String token = authorization.substring(BEARER_PREFIX.length());
            jwtTokenProvider.getSubject(token).ifPresent(subject -> authenticate(request, subject));
        }
        filterChain.doFilter(request, response);
    }

    private void authenticate(HttpServletRequest request, String subject) {
        if (!accessAuthorityService.isActiveUser(subject)) {
            return;
        }
        var authorities = accessAuthorityService.findAuthoritiesForActiveUser(subject);
        UsernamePasswordAuthenticationToken authentication =
                new UsernamePasswordAuthenticationToken(subject, null, authorities);
        authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
        SecurityContextHolder.getContext().setAuthentication(authentication);
    }
}
