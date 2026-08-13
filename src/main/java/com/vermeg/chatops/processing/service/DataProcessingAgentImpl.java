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
                resolveEnvironment(message),
                message.data(),
                message.tenant(),
                message.environmentType(),
                message.machineReference(),
                message.nodeRole(),
                message.jenkinsPurpose()
        );

        CanonicalEventEntity saved = repository.save(new CanonicalEventEntity(canonicalEvent));

        log.info(
                "Normalized and persisted event id={} agent={} env={} dataKeys={} tenant={} environmentType={} "
                        + "machineReference={} nodeRole={} jenkinsPurpose={}",
                saved.getId(), agentKey, canonicalEvent.environment(), message.data().keySet(),
                message.tenant(), message.environmentType(), message.machineReference(),
                message.nodeRole(), message.jenkinsPurpose()
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
        if (isBlank(message.tenant())) {
            throw new InvalidAgentMessageException("Missing 'tenant' in message from '" + agentKey + "'");
        }
        if (isBlank(message.environment())) {
            throw new InvalidAgentMessageException("Missing 'environment' in message from '" + agentKey + "'");
        }
        if (isBlank(message.environmentType())) {
            throw new InvalidAgentMessageException("Missing 'environmentType' in message from '" + agentKey + "'");
        }
        if (isBlank(message.machineReference())) {
            throw new InvalidAgentMessageException("Missing 'machineReference' in message from '" + agentKey + "'");
        }
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    /**
     * The environment an event belongs to.
     *
     * <p>{@code message.environment()} is validated as required above and is
     * the agent's own statement of which tenant environment it ran against, so
     * it wins. It previously was not consulted at all: resolution started at
     * the payload-internal {@code data.env} key and otherwise fell back to the
     * <em>server's</em> active Spring profile, which meant canonical_events
     * recorded where the backend was running rather than where the agent ran.
     * With the backend on the dev profile every event was stamped "dev"
     * regardless of its true environment, and on a prod backend the same rows
     * would all have read "prod".
     *
     * <p>The old sources are kept as fallbacks for messages predating the
     * top-level field.
     */
    private String resolveEnvironment(AgentMessage message) {
        if (message.environment() != null && !message.environment().isBlank()) {
            return message.environment();
        }
        Object rawEnv = message.data().get(ENV_DATA_KEY);
        if (rawEnv instanceof String s && !s.isBlank()) {
            return s;
        }
        String[] activeProfiles = springEnvironment.getActiveProfiles();
        return activeProfiles.length > 0 ? activeProfiles[0] : UNKNOWN_ENV;
    }
}