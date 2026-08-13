package com.vermeg.chatops.processing.service;

import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;

import java.util.List;

public interface AgentEventQueryService {

    /**
     * Resolves what the given user may see, from their active tenant
     * memberships and whether they hold the platform-wide scope.
     */
    AgentEventScope resolveScope(String userEmail, boolean hasPlatformWidePermission);

    List<AgentEventResponse> search(
            AgentEventScope scope,
            String agentKey,
            String tenant,
            String environment,
            int limit
    );

    /** One entry per agent this UI surfaces, whether or not it has ever reported. */
    List<AgentStatusResponse> findAgentStatuses(AgentEventScope scope);
}
