package com.vermeg.chatops.messaging.exception;

/**
 * Thrown when a publish is attempted for an agent key that has no queue
 * declared under {@code chatops.rabbitmq.queues}. Fail-fast: prevents
 * silently publishing to a routing key with no bound queue.
 */
public class UnknownAgentException extends RuntimeException {

    public UnknownAgentException(String agentKey) {
        super("Unknown agent '%s': no queue is configured for it".formatted(agentKey));
    }
}
