package com.vermeg.chatops.messaging.producer;

import java.util.Map;

/**
 * Publishes a message to the queue of the given agent, through the
 * topology declared in {@code RabbitMqConfiguration}.
 */
public interface AgentMessagePublisher {

    /**
     * @param agentKey key from {@code chatops.rabbitmq.queues} (e.g. "git", "jenkins")
     * @param data     arbitrary payload to wrap in the {@link com.vermeg.chatops.messaging.dto.AgentMessage} envelope
     * @throws com.vermeg.chatops.messaging.exception.UnknownAgentException if agentKey is not configured
     */
    void publish(String agentKey, Map<String, Object> data);
}
