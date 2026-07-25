package com.vermeg.chatops.messaging.consumer;

import com.vermeg.chatops.messaging.config.RabbitMqProperties;
import com.vermeg.chatops.messaging.dto.AgentMessage;
import java.util.Map;
import org.springframework.amqp.rabbit.annotation.RabbitListenerConfigurer;
import org.springframework.amqp.rabbit.listener.RabbitListenerEndpointRegistrar;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerEndpoint;
import org.springframework.amqp.rabbit.listener.adapter.MessageListenerAdapter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.stereotype.Component;

/**
 * Registers one listener endpoint per agent queue found in
 * {@code chatops.rabbitmq.queues}, without any per-agent Java code —
 * consistent with the data-driven topology declared in
 * {@code RabbitMqConfiguration} (Feature 1).
 *
 * <p>Each endpoint deserializes the message body into {@link AgentMessage}
 * (via the same {@link MessageConverter} bean used by the Producer) and
 * delegates to {@link AgentMessageHandler}, tagging it with the originating
 * agent key.
 *
 * <p>Note: with the default listener container, an exception thrown by the
 * handler causes the message to be requeued indefinitely — it is NOT yet
 * routed to the dead-letter queue on failure. Wiring retry limits + explicit
 * rejection to DLQ is the next messaging feature (Retry Strategy).
 */
@Component
public class AgentMessageListenerRegistrar implements RabbitListenerConfigurer {

    private static final String LISTENER_ID_SUFFIX = "-agent-listener";
    private static final String LISTENER_METHOD = "onMessage";

    private final RabbitMqProperties properties;
    private final MessageConverter jsonMessageConverter;
    private final AgentMessageHandler agentMessageHandler;

    public AgentMessageListenerRegistrar(
            RabbitMqProperties properties,
            MessageConverter jsonMessageConverter,
            AgentMessageHandler agentMessageHandler
    ) {
        this.properties = properties;
        this.jsonMessageConverter = jsonMessageConverter;
        this.agentMessageHandler = agentMessageHandler;
    }

    @Override
    public void configureRabbitListeners(RabbitListenerEndpointRegistrar registrar) {
        for (Map.Entry<String, String> entry : properties.getQueues().entrySet()) {
            registrar.registerEndpoint(buildEndpoint(entry.getKey(), entry.getValue()));
        }
    }

    private SimpleRabbitListenerEndpoint buildEndpoint(String agentKey, String queueName) {
        MessageListenerAdapter adapter = new MessageListenerAdapter(new AgentQueueDelegate(agentKey));
        adapter.setMessageConverter(jsonMessageConverter);
        adapter.setDefaultListenerMethod(LISTENER_METHOD);

        SimpleRabbitListenerEndpoint endpoint = new SimpleRabbitListenerEndpoint();
        endpoint.setId(agentKey + LISTENER_ID_SUFFIX);
        endpoint.setQueueNames(queueName);
        endpoint.setMessageListener(adapter);
        return endpoint;
    }

    /**
     * Binds a fixed agentKey to the generic handler so a single
     * {@link AgentMessageHandler} bean can serve every queue while still
     * knowing which agent each message came from.
     */
    private final class AgentQueueDelegate {

        private final String agentKey;

        private AgentQueueDelegate(String agentKey) {
            this.agentKey = agentKey;
        }

        @SuppressWarnings("unused") // invoked reflectively by MessageListenerAdapter
        public void onMessage(AgentMessage message) {
            agentMessageHandler.handle(agentKey, message);
        }
    }
}
