import { orchestratorBaseUrl, request } from "./apiClient"

/**
 * llm-orchestrator/api.py — ChatRequest. The orchestrator accepts exactly
 * these two fields and ignores anything else, so nothing else is sent.
 */
export interface ChatRequest {
  user_id: string
  message: string
}

/** llm-orchestrator/api.py — AgentStatus. */
export interface ChatAgentStatus {
  agent: string
  /** SUCCESS, FAILED, or NO_RESULT (planned but never reported back). */
  status: "SUCCESS" | "FAILED" | "NO_RESULT"
  error: string | null
}

/** llm-orchestrator/api.py — ChatResponse. */
export interface ChatResponse {
  answer: string
  mode: string
  tenant: string | null
  machine_reference: string | null
  agent_keys: string[]
  environment: string | null
  task_id: string | null
  conversation_saved: boolean
  /**
   * Per-agent outcome, so a failed agent can be shown as failed rather than
   * as "no data". Empty when the orchestrator launched no agent.
   */
  agent_statuses: ChatAgentStatus[]
}

/**
 * The orchestrator is a separate FastAPI process on its own port and has no
 * authentication of its own, so this call is anonymous by design rather than
 * by omission.
 *
 * Agent runs are subprocess launches that can take minutes, so the default
 * 30s client timeout is raised well past the orchestrator's own
 * AGENT_SUBPROCESS_TIMEOUT_SECONDS (300) plus its freshness wait.
 */
const CHAT_TIMEOUT_MS = 420000

export const chatApi = {
  send: (body: ChatRequest, signal?: AbortSignal) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body,
      anonymous: true,
      baseUrl: orchestratorBaseUrl(),
      timeoutMs: CHAT_TIMEOUT_MS,
      signal,
    }),

  health: () =>
    request<{ status: string }>("/health", {
      anonymous: true,
      baseUrl: orchestratorBaseUrl(),
      timeoutMs: 5000,
    }),
}
