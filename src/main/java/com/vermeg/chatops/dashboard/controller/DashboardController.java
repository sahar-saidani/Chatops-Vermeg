package com.vermeg.chatops.dashboard.controller;

import com.vermeg.chatops.access.service.TenantAccessQueryService;
import com.vermeg.chatops.conversation.entity.ConversationTurnEntity;
import com.vermeg.chatops.conversation.repository.ConversationTurnRepository;
import com.vermeg.chatops.dashboard.dto.DashboardResponse;
import com.vermeg.chatops.identity.repository.UserRepository;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;
import com.vermeg.chatops.processing.service.AgentEventQueryService;
import com.vermeg.chatops.tenancy.dto.TenantResponse;
import com.vermeg.chatops.tenancy.repository.EnvironmentRepository;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * Single aggregation call behind the dashboard, so the page makes one request
 * instead of five and never has to decide which of them it is allowed to make.
 *
 * <p>Every number here is counted from real rows. Nothing is estimated, and a
 * figure the caller may not see is omitted rather than zeroed.
 */
@RestController
@RequestMapping("/api/v1/dashboard")
public class DashboardController {

    private final TenantAccessQueryService tenantAccessQueryService;
    private final EnvironmentRepository environmentRepository;
    private final UserRepository userRepository;
    private final ConversationTurnRepository conversationTurnRepository;
    private final AgentEventQueryService agentEventQueryService;

    public DashboardController(
            TenantAccessQueryService tenantAccessQueryService,
            EnvironmentRepository environmentRepository,
            UserRepository userRepository,
            ConversationTurnRepository conversationTurnRepository,
            AgentEventQueryService agentEventQueryService
    ) {
        this.tenantAccessQueryService = tenantAccessQueryService;
        this.environmentRepository = environmentRepository;
        this.userRepository = userRepository;
        this.conversationTurnRepository = conversationTurnRepository;
        this.agentEventQueryService = agentEventQueryService;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public DashboardResponse summary(Authentication authentication) {
        List<TenantResponse> tenants = tenantAccessQueryService.findAssignedTenants(authentication.getName());

        int environmentCount = tenants.stream()
                .mapToInt(tenant -> environmentRepository.findAllByTenantId(tenant.id()).size())
                .sum();

        boolean canReadUsers = hasAuthority(authentication, "USER_READ");
        boolean canReadAgents = hasAuthority(authentication, "AGENT_EVENT_READ");

        // Same tenant scoping as GET /api/v1/agents/status: the dashboard must
        // not become a side channel for another tenant's agent activity.
        List<AgentStatusResponse> agents = canReadAgents
                ? agentEventQueryService.findAgentStatuses(agentEventQueryService.resolveScope(
                        authentication.getName(),
                        hasAuthority(authentication, "AGENT_EVENT_READ_ALL")))
                : List.of();

        return new DashboardResponse(
                tenants.size(),
                environmentCount,
                canReadUsers ? (int) userRepository.count() : null,
                conversationTurnRepository.countByNormalizedUserId(
                        ConversationTurnEntity.normalize(authentication.getName())
                ),
                canReadAgents,
                agents
        );
    }

    private static boolean hasAuthority(Authentication authentication, String authority) {
        return authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(authority::equals);
    }
}
