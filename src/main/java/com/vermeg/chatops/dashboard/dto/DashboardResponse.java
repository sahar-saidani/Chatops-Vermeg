package com.vermeg.chatops.dashboard.dto;

import com.vermeg.chatops.processing.dto.AgentStatusResponse;

import java.util.List;

/**
 * Everything the dashboard shows, scoped to the authenticated caller.
 *
 * <p>Counts the caller is not allowed to see are {@code null} rather than
 * zero, so the client can say "not available to you" instead of displaying a
 * confident and wrong zero. {@code agents} is empty for a caller without
 * AGENT_EVENT_READ, and {@code agentsVisible} says which of the two situations
 * an empty list represents.
 */
public record DashboardResponse(
        int tenantCount,
        int environmentCount,
        Integer userCount,
        long conversationCount,
        boolean agentsVisible,
        List<AgentStatusResponse> agents
) {
}
