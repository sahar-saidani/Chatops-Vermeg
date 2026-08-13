package com.vermeg.chatops.processing.controller;

import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;
import com.vermeg.chatops.processing.service.AgentEventQueryService;
import org.springframework.security.access.prepost.PreAuthorize;
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

    private final AgentEventQueryService agentEventQueryService;

    public AgentEventController(AgentEventQueryService agentEventQueryService) {
        this.agentEventQueryService = agentEventQueryService;
    }

    @GetMapping("/events")
    @PreAuthorize("hasAuthority('AGENT_EVENT_READ')")
    public List<AgentEventResponse> findEvents(
            @RequestParam(required = false) String agentKey,
            @RequestParam(required = false) String tenant,
            @RequestParam(required = false) String environment,
            @RequestParam(required = false) Integer limit
    ) {
        int effectiveLimit = limit == null ? DEFAULT_LIMIT : Math.min(Math.max(limit, 1), MAX_LIMIT);
        return agentEventQueryService.search(agentKey, tenant, environment, effectiveLimit);
    }

    @GetMapping("/status")
    @PreAuthorize("hasAuthority('AGENT_EVENT_READ')")
    public List<AgentStatusResponse> findAgentStatuses() {
        return agentEventQueryService.findAgentStatuses();
    }
}
