import { useState } from "react"
import { ChevronDown, ChevronRight, RefreshCw, MessageSquare } from "lucide-react"
import { historyApi } from "../api/historyApi"
import type { ConversationTurnResponse } from "../api/historyApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState } from "../components/DataState"
import { AGENT_LABELS } from "../types"
import type { AgentKey } from "../types"

/**
 * The caller's own conversation turns, persisted by the orchestrator through
 * POST /api/v1/conversations. There is no way to view another user's history:
 * the backend takes the owner from the authenticated principal.
 */
export default function HistoryPage() {
  const turns = useAsyncData<ConversationTurnResponse[]>(() => historyApi.list(100), [])

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>History</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            Your previous questions and the answers the agents produced.
          </p>
        </div>
        <button className="btn-secondary" onClick={turns.reload}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {turns.loading ? (
          <LoadingState label="Loading history..." />
        ) : turns.error !== null ? (
          <ErrorState error={turns.error} onRetry={turns.reload} />
        ) : (turns.data ?? []).length === 0 ? (
          <EmptyState
            title="No conversations yet"
            description="Questions you ask in AI Chat appear here once the orchestrator records them."
          />
        ) : (
          (turns.data ?? []).map(turn => <TurnRow key={turn.id} turn={turn} />)
        )}
      </div>
    </div>
  )
}

function TurnRow({ turn }: { turn: ConversationTurnResponse }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div style={{ borderBottom: "1px solid var(--border)" }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: "100%", display: "flex", alignItems: "flex-start", gap: 12,
          padding: "14px 18px", background: "none", border: "none",
          cursor: "pointer", textAlign: "left", color: "var(--foreground)",
        }}
      >
        <span style={{ marginTop: 2 }}>{expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
        <span style={{ flex: 1, minWidth: 0 }}>
          <span style={{
            display: "block", fontSize: 13.5, fontWeight: 600,
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          }}>
            {turn.userMessage}
          </span>
          <span style={{ display: "flex", gap: 10, flexWrap: "wrap", fontSize: 11.5, color: "var(--muted-foreground)", marginTop: 3 }}>
            <span>{new Date(turn.timestamp).toLocaleString()}</span>
            {turn.tenant && <span>{turn.tenant}</span>}
            {turn.environment && <span>{turn.environment}</span>}
            {turn.agentKeys.length > 0 && (
              <span>
                {turn.agentKeys.map(key => AGENT_LABELS[key as AgentKey] ?? key).join(", ")}
              </span>
            )}
          </span>
        </span>
      </button>

      {expanded && (
        <div style={{ padding: "0 18px 16px 44px", display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5, fontWeight: 700, color: "var(--muted-foreground)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              <MessageSquare size={11} /> Question
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>{turn.userMessage}</div>
          </div>
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--muted-foreground)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Answer
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{turn.assistantResponse}</div>
          </div>
        </div>
      )}
    </div>
  )
}
