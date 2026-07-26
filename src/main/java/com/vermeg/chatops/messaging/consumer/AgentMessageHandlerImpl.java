package com.vermeg.chatops.messaging.consumer;

import com.vermeg.chatops.messaging.dto.AgentMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class AgentMessageHandlerImpl implements AgentMessageHandler {

    private static final Logger log = LoggerFactory.getLogger(AgentMessageHandlerImpl.class);
    private static int attempts = 0;
    @Override
    public void handle(String agentKey, AgentMessage message) {
        attempts++;
        if (attempts < 2) { // échoue une fois, réussit à la 2e tentative
            throw new RuntimeException("Échec simulé tentative " + attempts);
        }
        log.info(
                "Received message from agent key '{}': agent={}, timestamp={}, dataKeys={}",
                agentKey, message.agent(), message.timestamp(), message.data().keySet()
        );
    }
}
