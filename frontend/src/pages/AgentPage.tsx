import { useState } from "react"
import { RefreshCw, ChevronDown, ChevronRight } from "lucide-react"
import { agentsApi } from "../api/agentsApi"
import type { AgentEventResponse, AgentStatusResponse } from "../api/agentsApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState } from "../components/DataState"
import AgentStatusCard from "../components/AgentStatusCard"
import { AGENT_LABELS } from "../types"
import type { AgentKey } from "../types"

const AGENT_DESCRIPTION: Record<AgentKey, string> = {
  git: "Repository activity, branches and commit history collected by git-agent.",
  jenkins: "Build and pipeline results collected by jenkins-agent.",
  installation: "Installed artifacts and configuration inventory collected by installation-agent.",
  log: "Log findings collected by log-agent.",
  infrastructure: "Host health and resource usage collected by infrastructure-agent.",
}

/**
 * One page per agent, reading the reports that agent published into
 * canonical_events. It shows the agent's own report payload verbatim rather
 * than a per-agent bespoke view, because each agent keeps its own shape and
 * inventing a normalized presentation would mean guessing at fields.
 */
export default function AgentPage({ agentKey }: { agentKey: AgentKey }) {
  const events = useAsyncData<AgentEventResponse[]>(
    () => agentsApi.events({ agentKey, limit: 50 }),
    [agentKey],
  )
  const statuses = useAsyncData<AgentStatusResponse[]>(() => agentsApi.statuses(), [])

  const status = (statuses.data ?? []).find(entry => entry.agentKey === agentKey) ?? null

  const reload = () => {
    events.reload()
    statuses.reload()
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>{AGENT_LABELS[agentKey]}</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2, maxWidth: 620, lineHeight: 1.6 }}>
            {AGENT_DESCRIPTION[agentKey]}
          </p>
        </div>
        <button className="btn-secondary" onClick={reload}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {statuses.loading ? (
        <LoadingState label="Loading agent status..." />
      ) : statuses.error !== null ? (
        <ErrorState error={statuses.error} onRetry={statuses.reload} />
      ) : status ? (
        <div style={{ maxWidth: 320 }}>
          <AgentStatusCard
            agentKey={agentKey}
            state={status.status}
            lastEventAt={status.lastEventAt}
            eventCount={status.eventCount}
            machineReference={status.machineReference}
            environment={status.environment}
            linkToDetail={false}
          />
        </div>
      ) : null}

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700 }}>Reports</h3>
        </div>

        {events.loading ? (
          <LoadingState label="Loading reports..." />
        ) : events.error !== null ? (
          <ErrorState error={events.error} onRetry={events.reload} />
        ) : (events.data ?? []).length === 0 ? (
          <EmptyState
            title="No reports yet"
            description={`No ${AGENT_LABELS[agentKey]} report has reached the platform. Ask a question in AI Chat to trigger a run.`}
          />
        ) : (
          <div>
            {(events.data ?? []).map(event => (
              <EventRow key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function EventRow({ event }: { event: AgentEventResponse }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div style={{ borderBottom: "1px solid var(--border)" }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 12,
          padding: "12px 18px", background: "none", border: "none",
          cursor: "pointer", textAlign: "left", color: "var(--foreground)",
        }}
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span style={{ fontSize: 13, fontWeight: 600, minWidth: 160 }}>
          {new Date(event.timestamp).toLocaleString()}
        </span>
        <span style={{ display: "flex", gap: 8, flexWrap: "wrap", fontSize: 12, color: "var(--muted-foreground)" }}>
          {event.tenant && <span>{event.tenant}</span>}
          {event.environment && <span>{event.environment}</span>}
          {event.machineReference && <span>{event.machineReference}</span>}
          {event.jenkinsPurpose && <span>{event.jenkinsPurpose}</span>}
        </span>
      </button>

      {expanded && (
        <pre style={{
          margin: 0, padding: "0 18px 16px 44px", fontSize: 12, fontFamily: "monospace",
          overflowX: "auto", color: "var(--muted-foreground)", whiteSpace: "pre-wrap",
        }}>
          {JSON.stringify(event.data, null, 2)}
        </pre>
      )}
    </div>
  )
}
