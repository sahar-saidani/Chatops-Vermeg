package com.vermeg.chatops.common.events;

import java.time.Instant;
import java.util.Map;

/**
 * Canonical, agent-agnostic event shape every downstream consumer (API,
 * dashboards, LLM) can rely on, regardless of which Collection Agent
 * (git, jenkins, oracle, ...) produced the original message.
 *
 * <p>Deliberately untyped on {@code data}: each agent keeps its own native
 * payload shape inside {@code data}; only the envelope (agent/timestamp/env)
 * is normalized at this stage. Field-level typing per agent is a later,
 * separate concern.
 */
public record CanonicalEvent(String agent, Instant timestamp, String environment, Map<String, Object> data) {
}