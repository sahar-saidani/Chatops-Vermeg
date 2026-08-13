import { apiClient } from "./apiClient"

/** com.vermeg.chatops.processing.dto.AgentEventResponse */
export interface AgentEventResponse {
  id: string
  agentKey: string
  timestamp: string
  tenant: string | null
  environment: string | null
  environmentType: string | null
  machineReference: string | null
  nodeRole: string | null
  jenkinsPurpose: string | null
  /** Each agent keeps its own payload shape; only the envelope is normalized. */
  data: Record<string, unknown>
}

/**
 * com.vermeg.chatops.processing.dto.AgentStatusResponse.
 *
 * The backend only ever returns NO_DATA, ONLINE or STALE, because those are
 * the only states provable from stored events. The wider AgentState union in
 * AgentStatusCard also covers states that come from a live chat run.
 */
export interface AgentStatusResponse {
  agentKey: string
  status: "NO_DATA" | "ONLINE" | "STALE"
  lastEventAt: string | null
  eventCount: number
  tenant: string | null
  environment: string | null
  machineReference: string | null
}

export interface AgentEventQuery {
  agentKey?: string
  tenant?: string
  environment?: string
  limit?: number
}

export const agentsApi = {
  events: (query: AgentEventQuery = {}) => {
    const params = new URLSearchParams()
    if (query.agentKey) params.set("agentKey", query.agentKey)
    if (query.tenant) params.set("tenant", query.tenant)
    if (query.environment) params.set("environment", query.environment)
    if (query.limit) params.set("limit", String(query.limit))
    const suffix = params.toString()
    return apiClient.get<AgentEventResponse[]>(`/api/v1/agents/events${suffix ? `?${suffix}` : ""}`)
  },

  statuses: () => apiClient.get<AgentStatusResponse[]>("/api/v1/agents/status"),
}
