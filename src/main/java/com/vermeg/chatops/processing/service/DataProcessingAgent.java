package com.vermeg.chatops.processing.service;

import com.vermeg.chatops.messaging.dto.AgentMessage;
import com.vermeg.chatops.processing.entity.CanonicalEventEntity;

/**
 * Single consumer-side entry point turning a raw, agent-specific
 * {@link AgentMessage} into the canonical event format
 * (agent/timestamp/environment/data) and persisting it.
 *
 * <p>If tomorrow a new Collection Agent is added (Kubernetes, AWS, ...),
 * it only needs to produce its own native JSON payload; this contract does
 * not change.
 */
public interface DataProcessingAgent {

    CanonicalEventEntity process(String agentKey, AgentMessage message);
}