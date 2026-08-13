import { apiClient } from "./apiClient"

/** com.vermeg.chatops.conversation.dto.ConversationTurnResponse */
export interface ConversationTurnResponse {
  id: string
  userId: string
  requestMode: string
  tenant: string | null
  environment: string | null
  agentKeys: string[]
  userMessage: string
  assistantResponse: string
  timestamp: string
}

/**
 * GET /api/v1/conversations returns the caller's own turns only; there is no
 * parameter to read anybody else's, by design.
 */
export const historyApi = {
  list: (limit?: number) =>
    apiClient.get<ConversationTurnResponse[]>(
      `/api/v1/conversations${limit ? `?limit=${limit}` : ""}`,
    ),
}
