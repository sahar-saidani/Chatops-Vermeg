import { useMemo, useState } from "react"
import { RefreshCw, Search, X, ChevronRight } from "lucide-react"
import { agentsApi } from "../api/agentsApi"
import type { AgentEventResponse } from "../api/agentsApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { useDebouncedValue } from "../hooks/useDebouncedValue"
import { EmptyState, ErrorState, LoadingState } from "../components/DataState"
import AgentStatusCard from "../components/AgentStatusCard"

/**
 * Dedicated view for log-agent events.
 *
 * The generic AgentPage renders each agent's payload as raw JSON, which is
 * unusable for logs: a single machine produces thousands of them. Every field
 * surfaced here was read from the payload log-agent actually publishes
 * (level, service, source, message, hostname, process, timestamp), so the
 * filters describe real data rather than an assumed schema. Anything the
 * payload does not carry is simply absent.
 */

interface LogRecord {
  eventId: string
  timestamp: string
  level: string
  service: string
  source: string
  message: string
  hostname: string
  process: string
  tenant: string | null
  machineReference: string | null
  raw: Record<string, unknown>
}

const LEVEL_STYLE: Record<string, { bg: string; color: string }> = {
  ERROR: { bg: "#fee2e2", color: "#dc2626" },
  WARN: { bg: "#fef3c7", color: "#d97706" },
  WARNING: { bg: "#fef3c7", color: "#d97706" },
  INFO: { bg: "#dbeafe", color: "#2563eb" },
  DEBUG: { bg: "#f3f4f6", color: "#6b7280" },
}

function readString(source: Record<string, unknown>, key: string): string {
  const value = source[key]
  return typeof value === "string" ? value : ""
}

function toLogRecord(event: AgentEventResponse): LogRecord {
  const data = event.data ?? {}
  return {
    eventId: event.id,
    // The payload carries its own timestamp; fall back to the envelope's.
    timestamp: readString(data, "timestamp") || event.timestamp,
    level: (readString(data, "level") || "UNKNOWN").toUpperCase(),
    service: readString(data, "service"),
    source: readString(data, "source"),
    message: readString(data, "message"),
    hostname: readString(data, "hostname"),
    process: readString(data, "process"),
    tenant: event.tenant,
    machineReference: event.machineReference,
    raw: data,
  }
}

export default function LogsPage() {
  const [search, setSearch] = useState("")
  const [level, setLevel] = useState("All")
  const [service, setService] = useState("All")
  const [since, setSince] = useState("")
  const [selected, setSelected] = useState<LogRecord | null>(null)

  // Thousands of log rows make per-keystroke re-filtering visible.
  const debouncedSearch = useDebouncedValue(search, 250)

  const events = useAsyncData<AgentEventResponse[]>(
    () => agentsApi.events({ agentKey: "log", limit: 200 }),
    [],
  )
  const statuses = useAsyncData(() => agentsApi.statuses(), [])
  const status = (statuses.data ?? []).find(entry => entry.agentKey === "log") ?? null

  const records = useMemo(() => (events.data ?? []).map(toLogRecord), [events.data])

  const levels = useMemo(
    () => ["All", ...Array.from(new Set(records.map(record => record.level))).sort()],
    [records],
  )
  const services = useMemo(
    () => ["All", ...Array.from(new Set(records.map(record => record.service).filter(Boolean))).sort()],
    [records],
  )

  const filtered = useMemo(() => {
    const needle = debouncedSearch.trim().toLowerCase()
    const sinceTime = since ? new Date(since).getTime() : null
    return records.filter(record => {
      if (level !== "All" && record.level !== level) return false
      if (service !== "All" && record.service !== service) return false
      if (sinceTime !== null) {
        const recordTime = new Date(record.timestamp).getTime()
        if (Number.isFinite(recordTime) && recordTime < sinceTime) return false
      }
      if (!needle) return true
      return (
        record.message.toLowerCase().includes(needle) ||
        record.source.toLowerCase().includes(needle) ||
        record.process.toLowerCase().includes(needle)
      )
    })
  }, [records, debouncedSearch, level, service, since])

  const reload = () => {
    events.reload()
    statuses.reload()
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>Logs</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2, maxWidth: 620, lineHeight: 1.6 }}>
            Log entries collected by log-agent and published to the platform.
          </p>
        </div>
        <button className="btn-secondary" onClick={reload}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {status && (
        <div style={{ maxWidth: 320 }}>
          <AgentStatusCard
            agentKey="log"
            state={status.status}
            lastEventAt={status.lastEventAt}
            eventCount={status.eventCount}
            machineReference={status.machineReference}
            environment={status.environment}
            linkToDetail={false}
          />
        </div>
      )}

      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 220, maxWidth: 320 }}>
          <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
          <input
            className="input-field"
            placeholder="Search message, source, process..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: 36 }}
          />
        </div>
        <select className="input-field" value={level} onChange={e => setLevel(e.target.value)} style={{ width: "auto", minWidth: 120 }}>
          {levels.map(value => <option key={value} value={value}>{value === "All" ? "All levels" : value}</option>)}
        </select>
        <select className="input-field" value={service} onChange={e => setService(e.target.value)} style={{ width: "auto", minWidth: 140 }}>
          {services.map(value => <option key={value} value={value}>{value === "All" ? "All services" : value}</option>)}
        </select>
        <input
          type="datetime-local"
          className="input-field"
          value={since}
          onChange={e => setSince(e.target.value)}
          title="Show entries at or after this time"
          style={{ width: "auto" }}
        />
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ padding: "12px 18px", borderBottom: "1px solid var(--border)", fontSize: 12.5, color: "var(--muted-foreground)" }}>
          {/* Says what is actually held client-side; it never claims to page through the full server-side history. */}
          Showing {filtered.length} of the {records.length} most recent entries retrieved
        </div>

        {events.loading ? (
          <LoadingState label="Loading logs..." />
        ) : events.error !== null ? (
          <ErrorState error={events.error} onRetry={events.reload} />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={records.length === 0 ? "No log entries" : "No matching entries"}
            description={
              records.length === 0
                ? "No log-agent report has reached the platform yet."
                : "No entry matches the current filters."
            }
          />
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th style={{ width: 170 }}>Time</th>
                <th style={{ width: 90 }}>Level</th>
                <th style={{ width: 140 }}>Service</th>
                <th>Message</th>
                <th style={{ width: 40 }}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(record => {
                const style = LEVEL_STYLE[record.level] ?? { bg: "var(--muted)", color: "var(--muted-foreground)" }
                return (
                  <tr
                    key={record.eventId}
                    onClick={() => setSelected(record)}
                    style={{ cursor: "pointer" }}
                  >
                    <td style={{ fontSize: 12.5, color: "var(--muted-foreground)", whiteSpace: "nowrap" }}>
                      {new Date(record.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <span className="badge" style={{ background: style.bg, color: style.color }}>{record.level}</span>
                    </td>
                    <td style={{ fontSize: 12.5 }}>{record.service || "—"}</td>
                    <td style={{ fontSize: 12.5, maxWidth: 520, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {record.message || "—"}
                    </td>
                    <td><ChevronRight size={13} color="var(--muted-foreground)" /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {selected && <LogDetailsDrawer record={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

function LogDetailsDrawer({ record, onClose }: { record: LogRecord; onClose: () => void }) {
  const fields: [string, string][] = [
    ["Time", new Date(record.timestamp).toLocaleString()],
    ["Level", record.level],
    ["Service", record.service || "—"],
    ["Source", record.source || "—"],
    ["Process", record.process || "—"],
    ["Host", record.hostname || "—"],
    ["Client", record.tenant ?? "—"],
    ["Machine", record.machineReference ?? "—"],
  ]

  return (
    <div
      style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.4)", display: "flex", justifyContent: "flex-end" }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <aside className="fade-in" style={{
        width: "min(560px, 100%)", height: "100%", background: "var(--card)",
        borderLeft: "1px solid var(--border)", display: "flex", flexDirection: "column",
      }}>
        <header style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700 }}>Log entry</h3>
          <button
            onClick={onClose}
            aria-label="Close details"
            style={{ background: "none", border: "1px solid var(--border)", borderRadius: 7, width: 30, height: 30, cursor: "pointer", color: "var(--muted-foreground)", display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            <X size={14} />
          </button>
        </header>

        <div style={{ padding: 20, overflowY: "auto", display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ display: "grid", gridTemplateColumns: "110px 1fr", rowGap: 8, columnGap: 12, fontSize: 13 }}>
            {fields.map(([label, value]) => (
              <div key={label} style={{ display: "contents" }}>
                <span style={{ color: "var(--muted-foreground)" }}>{label}</span>
                <span style={{ fontWeight: 500, wordBreak: "break-word" }}>{value}</span>
              </div>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>
              Message
            </div>
            <div style={{ fontSize: 13, lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {record.message || "—"}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>
              Raw payload
            </div>
            <pre style={{
              margin: 0, padding: 12, borderRadius: 8, background: "var(--muted)",
              border: "1px solid var(--border)", fontSize: 12, fontFamily: "monospace",
              overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word",
            }}>
              {JSON.stringify(record.raw, null, 2)}
            </pre>
          </div>
        </div>
      </aside>
    </div>
  )
}
