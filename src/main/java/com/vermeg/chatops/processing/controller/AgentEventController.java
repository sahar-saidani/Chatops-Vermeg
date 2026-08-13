package com.vermeg.chatops.processing.controller;

import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;
import com.vermeg.chatops.processing.service.AgentEventQueryService;
import com.vermeg.chatops.processing.service.AgentEventScope;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * Read access to the agent reports that RabbitMQ consumers land in
 * {@code canonical_events}. Before this, the only way to see an agent's output
 * was to read the local report files it writes on the machine it ran on.
 */
@RestController
@RequestMapping("/api/v1/agents")
public class AgentEventController {

    private static final int DEFAULT_LIMIT = 25;
    private static final int MAX_LIMIT = 200;
    /** Seeded by V12 and granted to ADMIN only; lets a caller read every tenant. */
    private static final String PLATFORM_WIDE_AUTHORITY = "AGENT_EVENT_READ_ALL";

    private final AgentEventQueryService agentEventQueryService;

    public AgentEventController(AgentEventQueryService agentEventQueryService) {
        this.agentEventQueryService = agentEventQueryService;
    }

    /**
     * AGENT_EVENT_READ authorizes reading agent reports; it does not decide
     * <em>whose</em>. Since canonical_events keeps every tenant's rows in one
     * table, the scope is resolved per caller and pushed into the query, so a
     * user can never read a tenant they are not a member of.
     */
    @GetMapping("/events")
    @PreAuthorize("hasAuthority('AGENT_EVENT_READ')")
    public List<AgentEventResponse> findEvents(
            Authentication authentication,
            @RequestParam(required = false) String agentKey,
            @RequestParam(required = false) String tenant,
            @RequestParam(required = false) String environment,
            @RequestParam(required = false) Integer limit
    ) {
        int effectiveLimit = limit == null ? DEFAULT_LIMIT : Math.min(Math.max(limit, 1), MAX_LIMIT);
        return agentEventQueryService.search(
                scopeFor(authentication), agentKey, tenant, environment, effectiveLimit);
    }

    @GetMapping("/status")
    @PreAuthorize("hasAuthority('AGENT_EVENT_READ')")
    public List<AgentStatusResponse> findAgentStatuses(Authentication authentication) {
        return agentEventQueryService.findAgentStatuses(scopeFor(authentication));
    }

    private AgentEventScope scopeFor(Authentication authentication) {
        boolean platformWide = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(PLATFORM_WIDE_AUTHORITY::equals);
        return agentEventQueryService.resolveScope(authentication.getName(), platformWide);
    }
}
