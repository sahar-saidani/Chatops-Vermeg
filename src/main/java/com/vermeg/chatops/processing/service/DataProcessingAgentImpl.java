package com.vermeg.chatops.processing.service;

import com.vermeg.chatops.common.events.CanonicalEvent;
import com.vermeg.chatops.messaging.dto.AgentMessage;
import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import com.vermeg.chatops.processing.exception.InvalidAgentMessageException;
import com.vermeg.chatops.processing.repository.CanonicalEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class DataProcessingAgentImpl implements DataProcessingAgent {

    private static final Logger log = LoggerFactory.getLogger(DataProcessingAgentImpl.class);
    private static final String ENV_DATA_KEY = "env";
    private static final String UNKNOWN_ENV = "unknown";

    private final CanonicalEventRepository repository;
    private final Environment springEnvironment;

    public DataProcessingAgentImpl(CanonicalEventRepository repository, Environment springEnvironment) {
        this.repository = repository;
        this.springEnvironment = springEnvironment;
    }

    @Override
    public CanonicalEventEntity process(String agentKey, AgentMessage message) {
        validate(agentKey, message);

        CanonicalEvent canonicalEvent = new CanonicalEvent(
                message.agent(),
                message.timestamp(),
                resolveEnvironment(message.data()),
                message.data()
        );

        CanonicalEventEntity saved = repository.save(new CanonicalEventEntity(canonicalEvent));

        log.info(
                "Normalized and persisted event id={} agent={} env={} dataKeys={}",
                saved.getId(), agentKey, canonicalEvent.environment(), message.data().keySet()
        );

        return saved;
    }

    private void validate(String agentKey, AgentMessage message) {
        if (agentKey == null || agentKey.isBlank()) {
            throw new InvalidAgentMessageException("Missing agent key");
        }
        if (message == null || message.agent() == null || message.agent().isBlank()) {
            throw new InvalidAgentMessageException("Missing 'agent' field in message from '" + agentKey + "'");
        }
        if (message.timestamp() == null) {
            throw new InvalidAgentMessageException("Missing 'timestamp' in message from '" + agentKey + "'");
        }
        if (message.data() == null) {
            throw new InvalidAgentMessageException("Missing 'data' payload in message from '" + agentKey + "'");
        }
    }

    private String resolveEnvironment(Map<String, Object> data) {
        Object rawEnv = data.get(ENV_DATA_KEY);
        if (rawEnv instanceof String s && !s.isBlank()) {
            return s;
        }
        String[] activeProfiles = springEnvironment.getActiveProfiles();
        return activeProfiles.length > 0 ? activeProfiles[0] : UNKNOWN_ENV;
    }
}