package com.vermeg.chatops.messaging.consumer;

import com.vermeg.chatops.messaging.dto.AgentMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class AgentMessageHandlerImpl implements AgentMessageHandler {

    private static final Logger log = LoggerFactory.getLogger(AgentMessageHandlerImpl.class);

    @Override
    public void handle(String agentKey, AgentMessage message) {
        log.info(
                "Received message from agent key '{}': agent={}, timestamp={}, dataKeys={}",
                agentKey, message.agent(), message.timestamp(), message.data().keySet()
        );
    }
}
