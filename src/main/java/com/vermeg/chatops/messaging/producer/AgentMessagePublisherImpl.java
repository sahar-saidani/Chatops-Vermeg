package com.vermeg.chatops.messaging.producer;

import com.vermeg.chatops.messaging.config.RabbitMqProperties;
import com.vermeg.chatops.messaging.dto.AgentMessage;
import com.vermeg.chatops.messaging.exception.UnknownAgentException;
import java.time.Instant;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

@Service
public class AgentMessagePublisherImpl implements AgentMessagePublisher {

    private static final Logger log = LoggerFactory.getLogger(AgentMessagePublisherImpl.class);

    private static final String ROUTING_KEY_PREFIX = "agent.";
    private static final String ROUTING_KEY_SUFFIX = ".data";
    private static final String AGENT_NAME_SUFFIX = "-agent";

    private final RabbitTemplate rabbitTemplate;
    private final RabbitMqProperties properties;

    public AgentMessagePublisherImpl(RabbitTemplate rabbitTemplate, RabbitMqProperties properties) {
        this.rabbitTemplate = rabbitTemplate;
        this.properties = properties;
    }

    @Override
    public void publish(String agentKey, Map<String, Object> data) {
        if (!properties.getQueues().containsKey(agentKey)) {
            throw new UnknownAgentException(agentKey);
        }

        String routingKey = ROUTING_KEY_PREFIX + agentKey + ROUTING_KEY_SUFFIX;
        AgentMessage message = new AgentMessage(agentKey + AGENT_NAME_SUFFIX, Instant.now(), data);

        log.info("Publishing message for agent '{}' with routing key '{}'", agentKey, routingKey);
        // rabbitTemplate.exchange is already set to chatops.agents.exchange (see RabbitMqConfiguration)
        rabbitTemplate.convertAndSend(routingKey, message);
    }
}
