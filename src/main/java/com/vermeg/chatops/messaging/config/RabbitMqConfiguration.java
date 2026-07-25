package com.vermeg.chatops.messaging.config;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Declarable;
import org.springframework.amqp.core.Declarables;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.annotation.EnableRabbit;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Declares the RabbitMQ topology used by the Agent Integration Layer:
 * one topic exchange fanning out to one durable queue per Python Agent,
 * each main queue backed by a dedicated dead-letter queue bound to a
 * shared dead-letter exchange.
 *
 * <p>Routing key convention: {@code agent.<agentKey>.data}
 * <p>Queue/DLQ names: taken from {@code chatops.rabbitmq.queues} (see
 * {@link RabbitMqProperties}). Adding a new agent = one new YAML entry,
 * no Java change, since topology is built from {@link Declarables}, the
 * Spring AMQP mechanism for declaring a variable number of elements from a
 * single {@code @Bean} method. {@code RabbitAdmin} auto-declares every
 * {@link Declarable} found on the context at startup.
 *
 * <p>Purely declarative: no business logic. Producer and Consumer
 * components (next features) depend on the beans declared here.
 */
@Configuration
@EnableRabbit
@EnableConfigurationProperties(RabbitMqProperties.class)
public class RabbitMqConfiguration {

    private static final String ROUTING_KEY_PREFIX = "agent.";
    private static final String ROUTING_KEY_SUFFIX = ".data";
    private static final String DLQ_SUFFIX = ".dlq";

    private final RabbitMqProperties properties;

    public RabbitMqConfiguration(RabbitMqProperties properties) {
        this.properties = properties;
    }

    @Bean
    TopicExchange agentsExchange() {
        return new TopicExchange(properties.getExchange(), true, false);
    }

    @Bean
    DirectExchange agentsDeadLetterExchange() {
        return new DirectExchange(properties.getDeadLetterExchange(), true, false);
    }

    /**
     * One main queue + one DLQ + two bindings per agent entry in
     * {@code chatops.rabbitmq.queues}, wrapped in a single {@link Declarables}
     * bean so RabbitAdmin declares all of them on the broker at startup.
     */
    @Bean
    Declarables agentQueueTopology() {
        List<Declarable> declarables = new ArrayList<>();

        for (Map.Entry<String, String> entry : properties.getQueues().entrySet()) {
            String agentKey = entry.getKey();
            String queueName = entry.getValue();
            String dlqName = queueName + DLQ_SUFFIX;
            String routingKey = ROUTING_KEY_PREFIX + agentKey + ROUTING_KEY_SUFFIX;

            Queue mainQueue = QueueBuilder.durable(queueName)
                    .withArgument("x-dead-letter-exchange", properties.getDeadLetterExchange())
                    .withArgument("x-dead-letter-routing-key", dlqName)
                    .build();

            Queue deadLetterQueue = QueueBuilder.durable(dlqName).build();

            Binding mainBinding = BindingBuilder.bind(mainQueue).to(agentsExchange()).with(routingKey);
            Binding dlqBinding = BindingBuilder.bind(deadLetterQueue).to(agentsDeadLetterExchange()).with(dlqName);

            declarables.add(mainQueue);
            declarables.add(deadLetterQueue);
            declarables.add(mainBinding);
            declarables.add(dlqBinding);
        }

        return new Declarables(declarables);
    }

    @Bean
    MessageConverter jsonMessageConverter() {
        return new Jackson2JsonMessageConverter();
    }

    @Bean
    RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory, MessageConverter jsonMessageConverter) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(jsonMessageConverter);
        template.setExchange(properties.getExchange());
        return template;
    }
}