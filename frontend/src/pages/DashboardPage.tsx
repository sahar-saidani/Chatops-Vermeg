import { Building2, Server, Users, MessageSquare, RefreshCw, Lock } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Link } from "react-router-dom"
import { dashboardApi } from "../api/dashboardApi"
import type { DashboardResponse } from "../api/dashboardApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState } from "../components/DataState"
import AgentStatusCard from "../components/AgentStatusCard"
import { useAuth } from "../context/AuthContext"
import { AGENT_KEYS } from "../types"
import type { AgentKey } from "../types"

/**
 * One dashboard for every role, built from GET /api/v1/dashboard.
 *
 * The previous build shipped three separate dashboards keyed off a fake
 * admin/devops/nondevops role, all filled with invented metrics. Roles are
 * database rows, so instead of branching on a role name the page shows the
 * figures the backend says this caller may see, and says so plainly when a
 * figure is withheld.
 *
 * ---------------------------------------------------------------------------
 * On "Admin / DevOps / Non-DevOps" dashboard variants
 * ---------------------------------------------------------------------------
 * Those three personas do not exist in this backend. The roles table holds
 * ADMIN, TENANT_ADMIN, USER, OPERATOR and AUDITOR, and none of them maps
 * cleanly onto "DevOps" or "Non-DevOps". Inventing that mapping in the
 * frontend would mean deciding, in TypeScript, something the RBAC model
 * deliberately keeps in the database.
 *
 * So the variation is driven by permissions instead, which is what actually
 * differs between those personas:
 *
 *   - the operations persona (ADMIN, OPERATOR) holds AGENT_EVENT_READ, so the
 *     Agents section renders; without it the section states that agent status
 *     is not available to this user rather than showing an empty grid
 *   - the administrative persona (ADMIN) holds USER_READ, so the Users tile
 *     shows a count; without it the tile renders an explicit no-access dash,
 *     never a zero
 *   - every caller sees their own tenants, environments and conversations
 *
 * The effect is the same set of dashboard variants the spec describes, keyed
 * to real permissions, and it keeps working when an administrator defines a
 * new role. The Sidebar filters navigation on the same principle.
 */
export default function DashboardPage() {
  const { user } = useAuth()
  const summary = useAsyncData<DashboardResponse>(() => dashboardApi.summary(), [])

  if (summary.loading) return <LoadingState label="Loading dashboard..." />
  if (summary.error !== null) return <ErrorState error={summary.error} onRetry={summary.reload} />

  const data = summary.data
  if (!data) return <EmptyState title="No dashboard data" />

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>
            Welcome back{user?.displayName ? `, ${user.displayName.split(" ")[0]}` : ""}
          </h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            An overview of what you have access to.
          </p>
        </div>
        <button className="btn-secondary" onClick={summary.reload}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        <MetricCard icon={Building2} label="Clients" value={data.tenantCount} to="/tenants" />
        <MetricCard icon={Server} label="Environments" value={data.environmentCount} to="/environments" />
        <MetricCard
          icon={Users}
          label="Users"
          value={data.userCount}
          to="/users"
          restricted={data.userCount === null}
        />
        <MetricCard icon={MessageSquare} label="Your conversations" value={data.conversationCount} to="/history" />
      </div>

      <div>
        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Agents</h3>
        {!data.agentsVisible ? (
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12 }}>
            <EmptyState
              title="Agent status not available to you"
              description="Viewing agent reports requires the AGENT_EVENT_READ permission."
            />
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 16 }}>
            {AGENT_KEYS.map(agentKey => {
              const status = data.agents.find(entry => entry.agentKey === agentKey)
              return (
                <AgentStatusCard
                  key={agentKey}
                  agentKey={agentKey as AgentKey}
                  state={status?.status ?? "NO_DATA"}
                  lastEventAt={status?.lastEventAt}
                  eventCount={status?.eventCount}
                  machineReference={status?.machineReference}
                  environment={status?.environment}
                />
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  to,
  restricted = false,
}: {
  icon: LucideIcon
  label: string
  value: number | null
  to: string
  restricted?: boolean
}) {
  const body = (
    <div className="metric-card" style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9,
          background: "color-mix(in srgb, var(--primary) 12%, transparent)",
          color: "var(--primary)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <Icon size={16} />
        </div>
        {restricted && <Lock size={13} color="var(--muted-foreground)" />}
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.03em" }}>
          {/* A withheld figure is never rendered as 0. */}
          {restricted || value === null ? "—" : value}
        </div>
        <div style={{ fontSize: 12.5, color: "var(--muted-foreground)", marginTop: 2 }}>
          {restricted ? `${label} (no access)` : label}
        </div>
      </div>
    </div>
  )

  if (restricted) return body
  return (
    <Link to={to} style={{ textDecoration: "none", color: "inherit", display: "block", height: "100%" }}>
      {body}
    </Link>
  )
}
