package com.vermeg.chatops.processing.dto;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * A single agent report as stored in {@code canonical_events}.
 *
 * <p>{@code data} stays untyped for the same reason it is untyped on
 * {@link com.vermeg.chatops.common.events.CanonicalEvent}: each agent keeps
 * its own native payload shape, and only the envelope is normalized.
 */
public record AgentEventResponse(
        UUID id,
        String agentKey,
        Instant timestamp,
        String tenant,
        String environment,
        String environmentType,
        String machineReference,
        String nodeRole,
        String jenkinsPurpose,
        Map<String, Object> data
) {
}
