package com.vermeg.chatops.processing.service;

import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;

import java.util.List;

public interface AgentEventQueryService {

    List<AgentEventResponse> search(String agentKey, String tenant, String environment, int limit);

    /** One entry per agent this UI surfaces, whether or not it has ever reported. */
    List<AgentStatusResponse> findAgentStatuses();
}
