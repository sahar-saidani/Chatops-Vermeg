package com.vermeg.chatops.messaging.dto;

import java.time.Instant;
import java.util.Map;

/**
 * Standard multi-agent message envelope.
 *
 * <p>Mirrors the Python-side {@code AgentMessage} pydantic model
 * ({@code agent: str, timestamp: datetime, data: dict}) used by the agents
 * (see {@code jenkins-agent/models/schemas.py}), so that JSON produced here
 * is structurally compatible with what the agents already emit.
 */
public record AgentMessage(String agent, Instant timestamp, Map<String, Object> data) {
}
