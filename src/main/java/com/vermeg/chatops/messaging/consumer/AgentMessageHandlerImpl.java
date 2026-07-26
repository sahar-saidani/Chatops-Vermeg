package com.vermeg.chatops.messaging.consumer;

import com.vermeg.chatops.messaging.dto.AgentMessage;
import com.vermeg.chatops.processing.service.DataProcessingAgent;
import org.springframework.stereotype.Component;

/**
 * Thin adapter: delegates every consumed message to the Data Processing
 * Agent, which is now the real consumer-side business logic (validation,
 * normalization, persistence).
 */
@Component
public class AgentMessageHandlerImpl implements AgentMessageHandler {

    private final DataProcessingAgent dataProcessingAgent;

    public AgentMessageHandlerImpl(DataProcessingAgent dataProcessingAgent) {
        this.dataProcessingAgent = dataProcessingAgent;
    }

    @Override
    public void handle(String agentKey, AgentMessage message) {
        dataProcessingAgent.process(agentKey, message);
    }
}