package com.vermeg.chatops.processing.service;

import com.vermeg.chatops.access.service.TenantAccessQueryService;
import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;
import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import com.vermeg.chatops.processing.repository.CanonicalEventRepository;
import com.vermeg.chatops.tenancy.dto.TenantResponse;
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
    private final TenantAccessQueryService tenantAccessQueryService;

    public AgentEventQueryServiceImpl(
            CanonicalEventRepository canonicalEventRepository,
            TenantAccessQueryService tenantAccessQueryService
    ) {
        this.canonicalEventRepository = canonicalEventRepository;
        this.tenantAccessQueryService = tenantAccessQueryService;
    }

    @Override
    public AgentEventScope resolveScope(String userEmail, boolean hasPlatformWidePermission) {
        if (hasPlatformWidePermission) {
            return AgentEventScope.allTenants();
        }
        // canonical_events.tenant stores the tenant *name*, and tenants.name is
        // unique as of V8, so the name is a safe join key here.
        List<String> tenantNames = tenantAccessQueryService.findAssignedTenants(userEmail).stream()
                .map(TenantResponse::name)
                .toList();
        return AgentEventScope.forTenants(tenantNames);
    }

    @Override
    public List<AgentEventResponse> search(
            AgentEventScope scope,
            String agentKey,
            String tenant,
            String environment,
            int limit
    ) {
        // A caller belonging to no tenant sees nothing. Returning early also
        // keeps an empty IN () list out of the query.
        if (scope.isEmpty()) {
            return List.of();
        }

        PageRequest page = PageRequest.of(0, limit);
        List<CanonicalEventEntity> events = scope.platformWide()
                ? canonicalEventRepository.search(
                        blankToNull(agentKey), blankToNull(tenant), blankToNull(environment), page)
                : canonicalEventRepository.searchForTenants(
                        scope.tenantNames(),
                        blankToNull(agentKey),
                        blankToNull(tenant),
                        blankToNull(environment),
                        page);

        return events.stream().map(AgentEventQueryServiceImpl::toResponse).toList();
    }

    @Override
    public List<AgentStatusResponse> findAgentStatuses(AgentEventScope scope) {
        Instant now = Instant.now();
        return SURFACED_AGENT_KEYS.stream()
                .map(agentKey -> toStatus(agentKey, scope, now))
                .toList();
    }

    private AgentStatusResponse toStatus(String agentKey, AgentEventScope scope, Instant now) {
        if (scope.isEmpty()) {
            return new AgentStatusResponse(agentKey, "NO_DATA", null, 0L, null, null, null);
        }

        PageRequest newest = PageRequest.of(0, 1);
        List<CanonicalEventEntity> latest = scope.platformWide()
                ? canonicalEventRepository.findByAgentKeyOrderByMessageTimestampDesc(agentKey, newest)
                : canonicalEventRepository.findByAgentKeyAndTenantInOrderByMessageTimestampDesc(
                        agentKey, scope.tenantNames(), newest);

        if (latest.isEmpty()) {
            // No rows means "never reported", which is emphatically not the
            // same as "reported a failure". Callers must render it as such.
            return new AgentStatusResponse(agentKey, "NO_DATA", null, 0L, null, null, null);
        }

        CanonicalEventEntity event = latest.get(0);
        long count = scope.platformWide()
                ? canonicalEventRepository.countByAgentKey(agentKey)
                : canonicalEventRepository.countByAgentKeyAndTenantIn(agentKey, scope.tenantNames());

        boolean fresh = Duration.between(event.getMessageTimestamp(), now).compareTo(FRESHNESS_WINDOW) <= 0;
        return new AgentStatusResponse(
                agentKey,
                fresh ? "ONLINE" : "STALE",
                event.getMessageTimestamp(),
                count,
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
