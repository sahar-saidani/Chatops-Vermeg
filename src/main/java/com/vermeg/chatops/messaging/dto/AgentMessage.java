package com.vermeg.chatops.messaging.dto;

import java.time.Instant;
import java.util.Map;

/**
 * Standard multi-agent message envelope.
 *
 * <p>Mirrors the Python-side {@code AgentMessage} pydantic model used by the
 * agents (see {@code jenkins-agent/models/schemas.py}), so that JSON produced
 * here is structurally compatible with what the agents already emit.
 *
 * <p>{@code tenant}/{@code environment}/{@code environmentType}/
 * {@code machineReference} are populated by every agent as of the RabbitMQ
 * publishing enrichment; {@code nodeRole} (CLUSTER environments only) and
 * {@code jenkinsPurpose} (jenkins-agent only) are present only when
 * applicable and are otherwise {@code null}.
 */
public record AgentMessage(
        String agent,
        Instant timestamp,
        Map<String, Object> data,
        String tenant,
        String environment,
        String environmentType,
        String machineReference,
        String nodeRole,
        String jenkinsPurpose
) {
}
