package com.vermeg.chatops.security.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

/**
 * Browser origins allowed to call the API.
 *
 * <p>Configured through {@code chatops.cors.allowed-origins} so each
 * environment declares its own frontend origin instead of hardcoding the dev
 * one. Wildcards are deliberately unsupported: the API answers with
 * {@code Access-Control-Allow-Credentials: true}, and the CORS spec forbids
 * combining that with {@code *}.
 */
@ConfigurationProperties(prefix = "chatops.cors")
public record CorsProperties(
        List<String> allowedOrigins,
        List<String> allowedMethods,
        List<String> allowedHeaders,
        Long maxAgeSeconds
) {

    private static final List<String> DEFAULT_METHODS =
            List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS");
    private static final List<String> DEFAULT_HEADERS =
            List.of("Authorization", "Content-Type", "Accept", "X-Requested-With");
    private static final long DEFAULT_MAX_AGE_SECONDS = 3600L;

    public CorsProperties {
        allowedOrigins = allowedOrigins == null || allowedOrigins.isEmpty()
                ? List.of("http://localhost:5173")
                : List.copyOf(allowedOrigins);
        allowedMethods = allowedMethods == null || allowedMethods.isEmpty()
                ? DEFAULT_METHODS
                : List.copyOf(allowedMethods);
        allowedHeaders = allowedHeaders == null || allowedHeaders.isEmpty()
                ? DEFAULT_HEADERS
                : List.copyOf(allowedHeaders);
        maxAgeSeconds = maxAgeSeconds == null ? DEFAULT_MAX_AGE_SECONDS : maxAgeSeconds;
    }
}
