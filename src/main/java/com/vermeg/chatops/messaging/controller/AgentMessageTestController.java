package com.vermeg.chatops.messaging.controller;

import com.vermeg.chatops.messaging.producer.AgentMessagePublisher;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Manual verification endpoint for the RabbitMQ Agent Integration Layer.
 *
 * <p>Purely delegates to {@link AgentMessagePublisher} — no business logic,
 * no dashboard/report/notification concern. Its only purpose is to exercise
 * the messaging layer (topology + producer) end-to-end from a real HTTP
 * call instead of the RabbitMQ management UI. Requires authentication like
 * every other endpoint (no change to SecurityConfiguration was needed).
 */
@RestController
@RequestMapping("/api/v1/messaging/agents")
public class AgentMessageTestController {

    private final AgentMessagePublisher agentMessagePublisher;

    public AgentMessageTestController(AgentMessagePublisher agentMessagePublisher) {
        this.agentMessagePublisher = agentMessagePublisher;
    }

    @PostMapping("/{agentKey}/publish")
    public ResponseEntity<Void> publish(@PathVariable String agentKey, @RequestBody Map<String, Object> data) {
        agentMessagePublisher.publish(agentKey, data);
        return ResponseEntity.accepted().build();
    }
}
