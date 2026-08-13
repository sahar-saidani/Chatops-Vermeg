import {
  Activity, AlertTriangle, CheckCircle2, CircleSlash, Clock,
  GitBranch, Hammer, Loader2, Package, ScrollText, Inbox,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Link } from "react-router-dom"
import { AGENT_LABELS } from "../types"
import type { AgentKey } from "../types"

/**
 * Every state an agent can be in, in one place.
 *
 * ONLINE / STALE / NO_DATA come from stored canonical_events.
 * RUNNING / SUCCESS / FAILED / TIMEOUT describe a live orchestrator run.
 * DISABLED means the agent is not available for the selected client.
 *
 * FAILED and TIMEOUT are visually distinct from NO_DATA on purpose: an agent
 * that broke and an agent that ran and found nothing are different answers,
 * and showing a failure as "no data" is the specific bug this component
 * exists to prevent.
 */
export type AgentState =
  | "ONLINE"
  | "STALE"
  | "RUNNING"
  | "SUCCESS"
  | "FAILED"
  | "TIMEOUT"
  | "NO_DATA"
  | "DISABLED"

const STATE_STYLE: Record<AgentState, { label: string; bg: string; color: string; icon: LucideIcon }> = {
  ONLINE: { label: "Online", bg: "#dcfce7", color: "#16a34a", icon: CheckCircle2 },
  SUCCESS: { label: "Success", bg: "#dcfce7", color: "#16a34a", icon: CheckCircle2 },
  RUNNING: { label: "Running", bg: "#dbeafe", color: "#2563eb", icon: Loader2 },
  STALE: { label: "Stale", bg: "#fef3c7", color: "#d97706", icon: Clock },
  TIMEOUT: { label: "Timed out", bg: "#ffedd5", color: "#ea580c", icon: Clock },
  FAILED: { label: "Failed", bg: "#fee2e2", color: "#dc2626", icon: AlertTriangle },
  NO_DATA: { label: "No data", bg: "#f3f4f6", color: "#6b7280", icon: Inbox },
  DISABLED: { label: "Disabled", bg: "#f3f4f6", color: "#9ca3af", icon: CircleSlash },
}

const AGENT_ICON: Record<AgentKey, LucideIcon> = {
  git: GitBranch,
  jenkins: Hammer,
  installation: Package,
  log: ScrollText,
  infrastructure: Activity,
}

const AGENT_ROUTE: Record<AgentKey, string> = {
  git: "/git",
  jenkins: "/jenkins",
  installation: "/installation",
  log: "/logs",
  infrastructure: "/infrastructure",
}

export interface AgentStatusCardProps {
  agentKey: AgentKey
  state: AgentState
  lastEventAt?: string | null
  eventCount?: number
  machineReference?: string | null
  environment?: string | null
  /** Shown under the badge when the state is FAILED or TIMEOUT. */
  detail?: string | null
  linkToDetail?: boolean
}

function describeState(props: AgentStatusCardProps): string {
  switch (props.state) {
    case "NO_DATA":
      return "This agent has never delivered a report."
    case "STALE":
      return "The most recent report is over a day old."
    case "FAILED":
      return props.detail ?? "The last run failed."
    case "TIMEOUT":
      return props.detail ?? "The last run exceeded its time limit."
    case "RUNNING":
      return "A run is in progress."
    case "DISABLED":
      return "Not available for this client."
    default:
      return props.lastEventAt
        ? `Last report ${new Date(props.lastEventAt).toLocaleString()}`
        : "Reporting normally."
  }
}

export default function AgentStatusCard(props: AgentStatusCardProps) {
  const { agentKey, state, eventCount, machineReference, environment, linkToDetail = true } = props
  const style = STATE_STYLE[state]
  const AgentIcon = AGENT_ICON[agentKey]
  const StateIcon = style.icon

  const card = (
    <div className="metric-card" style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 9,
          background: "color-mix(in srgb, var(--primary) 12%, transparent)",
          color: "var(--primary)",
          display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        }}>
          <AgentIcon size={17} />
        </div>
        <span className="badge" style={{ background: style.bg, color: style.color, gap: 4 }}>
          <StateIcon size={10} />
          {style.label}
        </span>
      </div>

      <div>
        <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em" }}>{AGENT_LABELS[agentKey]}</div>
        <div style={{ fontSize: 12.5, color: "var(--muted-foreground)", marginTop: 4, lineHeight: 1.5 }}>
          {describeState(props)}
        </div>
      </div>

      {(machineReference || environment || typeof eventCount === "number") && (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", fontSize: 11.5, color: "var(--muted-foreground)" }}>
          {machineReference && <span>{machineReference}</span>}
          {environment && <span>{environment}</span>}
          {typeof eventCount === "number" && (
            <span>{eventCount} report{eventCount === 1 ? "" : "s"}</span>
          )}
        </div>
      )}
    </div>
  )

  if (!linkToDetail) return card
  return (
    <Link to={AGENT_ROUTE[agentKey]} style={{ textDecoration: "none", color: "inherit", display: "block", height: "100%" }}>
      {card}
    </Link>
  )
}
