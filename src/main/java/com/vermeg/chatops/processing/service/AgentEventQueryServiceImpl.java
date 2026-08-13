package com.vermeg.chatops.processing.service;

import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;
import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import com.vermeg.chatops.processing.repository.CanonicalEventRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

@Service
@Transactional(readOnly = true)
public class AgentEventQueryServiceImpl implements AgentEventQueryService {

    /**
     * The agent keys this platform surfaces. Matches the queue names under
     * chatops.rabbitmq.queues, minus jira: jira-agent exists and keeps
     * publishing, but is deliberately not exposed through this API.
     */
    private static final List<String> SURFACED_AGENT_KEYS =
            List.of("git", "jenkins", "installation", "log", "infrastructure");

    /** Beyond this, the newest report is reported as STALE rather than ONLINE. */
    private static final Duration FRESHNESS_WINDOW = Duration.ofHours(24);

    private final CanonicalEventRepository canonicalEventRepository;

    public AgentEventQueryServiceImpl(CanonicalEventRepository canonicalEventRepository) {
        this.canonicalEventRepository = canonicalEventRepository;
    }

    @Override
    public List<AgentEventResponse> search(String agentKey, String tenant, String environment, int limit) {
        return canonicalEventRepository
                .search(blankToNull(agentKey), blankToNull(tenant), blankToNull(environment), PageRequest.of(0, limit))
                .stream()
                .map(AgentEventQueryServiceImpl::toResponse)
                .toList();
    }

    @Override
    public List<AgentStatusResponse> findAgentStatuses() {
        Instant now = Instant.now();
        return SURFACED_AGENT_KEYS.stream()
                .map(agentKey -> toStatus(agentKey, now))
                .toList();
    }

    private AgentStatusResponse toStatus(String agentKey, Instant now) {
        List<CanonicalEventEntity> latest =
                canonicalEventRepository.findByAgentKeyOrderByMessageTimestampDesc(agentKey, PageRequest.of(0, 1));

        if (latest.isEmpty()) {
            // No rows means "never reported", which is emphatically not the
            // same as "reported a failure". Callers must render it as such.
            return new AgentStatusResponse(agentKey, "NO_DATA", null, 0L, null, null, null);
        }

        CanonicalEventEntity event = latest.get(0);
        boolean fresh = Duration.between(event.getMessageTimestamp(), now).compareTo(FRESHNESS_WINDOW) <= 0;
        return new AgentStatusResponse(
                agentKey,
                fresh ? "ONLINE" : "STALE",
                event.getMessageTimestamp(),
                canonicalEventRepository.countByAgentKey(agentKey),
                event.getTenant(),
                event.getEnvironment(),
                event.getMachineReference()
        );
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private static AgentEventResponse toResponse(CanonicalEventEntity entity) {
        return new AgentEventResponse(
                entity.getId(),
                entity.getAgentKey(),
                entity.getMessageTimestamp(),
                entity.getTenant(),
                entity.getEnvironment(),
                entity.getEnvironmentType(),
                entity.getMachineReference(),
                entity.getNodeRole(),
                entity.getJenkinsPurpose(),
                entity.getData()
        );
    }
}
