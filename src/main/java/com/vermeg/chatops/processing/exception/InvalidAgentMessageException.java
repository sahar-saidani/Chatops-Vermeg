package com.vermeg.chatops.processing.exception;

/**
 * Thrown when a raw agent message fails validation (missing agent key,
 * timestamp, or data payload). Left unrejected explicitly here so it
 * propagates to the listener container: it is retried per
 * {@code spring.rabbitmq.listener.simple.retry}, then routed to the
 * dead-letter queue once retries are exhausted, same as any other
 * processing failure.
 */
public class InvalidAgentMessageException extends RuntimeException {

  public InvalidAgentMessageException(String message) {
    super(message);
  }
}