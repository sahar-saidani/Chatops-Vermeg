package com.vermeg.chatops.messaging.config;

import java.util.Map;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Externalized RabbitMQ topology configuration.
 *
 * <p>Bound from {@code chatops.rabbitmq.*} in application.yml. Adding a new
 * Python Agent only requires a new entry in {@code queues}; no Java code
 * change is needed.
 */
@ConfigurationProperties(prefix = "chatops.rabbitmq")
public class RabbitMqProperties {

    /** Main topic exchange all agent messages are published to. */
    private String exchange;

    /** Dead-letter exchange messages are routed to after retries are exhausted. */
    private String deadLetterExchange = "chatops.agents.dlx";

    /** agentKey -> queue name (e.g. "git" -> "chatops.agent.git.queue"). */
    private Map<String, String> queues;
    private String deadLetterSuffix = ".dlq";



    public String getExchange() {
        return exchange;
    }

    public void setExchange(String exchange) {
        this.exchange = exchange;
    }

    public String getDeadLetterExchange() {
        return deadLetterExchange;
    }

    public void setDeadLetterExchange(String deadLetterExchange) {
        this.deadLetterExchange = deadLetterExchange;
    }

    public Map<String, String> getQueues() {
        return queues;
    }

    public void setQueues(Map<String, String> queues) {
        this.queues = queues;
    }
    public String getDeadLetterSuffix() {
        return deadLetterSuffix;
    }

    public void setDeadLetterSuffix(String deadLetterSuffix) {
        this.deadLetterSuffix = deadLetterSuffix;
    }


}