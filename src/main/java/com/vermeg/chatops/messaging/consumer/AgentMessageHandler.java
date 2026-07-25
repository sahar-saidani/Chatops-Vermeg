package com.vermeg.chatops.messaging.consumer;

import com.vermeg.chatops.messaging.dto.AgentMessage;

/**
 * Handles a message received from an agent's queue.
 *
 * <p>Intentionally thin at this stage: only structured logging. Real
 * business processing (persistence, dashboard updates, notifications) is
 * explicitly out of scope for the RabbitMQ Integration Layer and will be
 * wired in by a future module through this same interface.
 */
public interface AgentMessageHandler {

    void handle(String agentKey, AgentMessage message);
}
