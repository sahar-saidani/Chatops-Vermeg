import { apiClient } from "./apiClient"
import type { AgentStatusResponse } from "./agentsApi"

/**
 * com.vermeg.chatops.dashboard.dto.DashboardResponse.
 *
 * userCount is null when the caller lacks USER_READ, and agentsVisible
 * distinguishes "no agent has ever reported" from "you may not see agents" --
 * both of which would otherwise arrive as an empty list.
 */
export interface DashboardResponse {
  tenantCount: number
  environmentCount: number
  userCount: number | null
  conversationCount: number
  agentsVisible: boolean
  agents: AgentStatusResponse[]
}

export const dashboardApi = {
  summary: () => apiClient.get<DashboardResponse>("/api/v1/dashboard"),
}
