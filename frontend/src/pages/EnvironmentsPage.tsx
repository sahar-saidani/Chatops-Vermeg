import { useEffect, useState } from "react"
import { Plus, Pencil, Trash2, AlertTriangle } from "lucide-react"
import { environmentsApi } from "../api/environmentsApi"
import { tenantsApi } from "../api/tenantsApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState, describeError } from "../components/DataState"
import PermissionGate from "../components/PermissionGate"
import { PERMISSIONS } from "../types"
import type { EnvironmentResponse, EnvironmentType } from "../types/api"

const ENVIRONMENT_TYPES: EnvironmentType[] = ["STANDALONE", "CLUSTER"]

/**
 * Environments live under /api/v1/tenants/{tenantId}/environments -- there is
 * no global list endpoint -- so the page requires a selected client and shows
 * that client's environments.
 */
export default function EnvironmentsPage() {
  const tenants = useAsyncData(() => tenantsApi.list(), [])
  const [tenantId, setTenantId] = useState("")
  const [editing, setEditing] = useState<EnvironmentResponse | null>(null)
  const [creating, setCreating] = useState(false)
  const [actionError, setActionError] = useState<unknown>(null)

  useEffect(() => {
    const list = tenants.data ?? []
    if (!tenantId && list.length > 0) setTenantId(list[0].id)
  }, [tenants.data, tenantId])

  const environments = useAsyncData<EnvironmentResponse[]>(
    () => (tenantId ? environmentsApi.list(tenantId) : Promise.resolve([])),
    [tenantId],
  )

  const remove = async (environment: EnvironmentResponse) => {
    setActionError(null)
    try {
      await environmentsApi.remove(tenantId, environment.id)
      environments.reload()
    } catch (error) {
      setActionError(error)
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>Environments</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            Deployment environments defined for a client.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {(tenants.data ?? []).length > 0 && (
            <select
              className="input-field"
              value={tenantId}
              onChange={e => setTenantId(e.target.value)}
              style={{ width: "auto", minWidth: 180 }}
            >
              {(tenants.data ?? []).map(tenant => (
                <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
              ))}
            </select>
          )}
          <PermissionGate anyOf={[PERMISSIONS.environmentCreate]}>
            <button className="btn-primary" onClick={() => setCreating(true)} disabled={!tenantId}>
              <Plus size={14} /> New environment
            </button>
          </PermissionGate>
        </div>
      </div>

      {actionError !== null && (
        <div style={{
          display: "flex", gap: 10, padding: "10px 14px", borderRadius: 8,
          background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b", fontSize: 13,
        }}>
          <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
          <span>{describeError(actionError)}</span>
        </div>
      )}

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {tenants.loading ? (
          <LoadingState label="Loading clients..." />
        ) : tenants.error !== null ? (
          <ErrorState error={tenants.error} onRetry={tenants.reload} />
        ) : (tenants.data ?? []).length === 0 ? (
          <EmptyState
            title="No client assigned"
            description="Environments belong to a client. You are not a member of any client yet."
          />
        ) : environments.loading ? (
          <LoadingState label="Loading environments..." />
        ) : environments.error !== null ? (
          <ErrorState error={environments.error} onRetry={environments.reload} />
        ) : (environments.data ?? []).length === 0 ? (
          <EmptyState title="No environments" description="This client has no environment defined yet." />
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th>Environment</th>
                <th>Type</th>
                <th>Client</th>
                <th>Created</th>
                <th style={{ width: 110 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(environments.data ?? []).map(environment => (
                <tr key={environment.id}>
                  <td style={{ fontSize: 13.5, fontWeight: 600 }}>{environment.name}</td>
                  <td>
                    <span className="badge" style={{
                      background: environment.type === "CLUSTER" ? "#dbeafe" : "#ede9fe",
                      color: environment.type === "CLUSTER" ? "#2563eb" : "#4f46e5",
                    }}>
                      {environment.type.toLowerCase()}
                    </span>
                  </td>
                  <td style={{ fontSize: 13 }}>{environment.tenant.name}</td>
                  <td style={{ fontSize: 13, color: "var(--muted-foreground)" }}>
                    {new Date(environment.createdAt).toLocaleDateString()}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 4 }}>
                      <PermissionGate anyOf={[PERMISSIONS.environmentUpdate]}>
                        <button title="Edit" onClick={() => setEditing(environment)} style={{
                          width: 28, height: 28, borderRadius: 6, border: "1px solid var(--border)",
                          background: "none", cursor: "pointer", display: "flex",
                          alignItems: "center", justifyContent: "center", color: "var(--muted-foreground)",
                        }}>
                          <Pencil size={13} />
                        </button>
                      </PermissionGate>
                      <PermissionGate anyOf={[PERMISSIONS.environmentDelete]}>
                        <button title="Delete" onClick={() => remove(environment)} style={{
                          width: 28, height: 28, borderRadius: 6, border: "1px solid var(--border)",
                          background: "none", cursor: "pointer", display: "flex",
                          alignItems: "center", justifyContent: "center", color: "#dc2626",
                        }}>
                          <Trash2 size={13} />
                        </button>
                      </PermissionGate>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {(creating || editing) && tenantId && (
        <EnvironmentModal
          tenantId={tenantId}
          environment={editing}
          onClose={() => {
            setCreating(false)
            setEditing(null)
          }}
          onSaved={() => {
            setCreating(false)
            setEditing(null)
            environments.reload()
          }}
        />
      )}
    </div>
  )
}

function EnvironmentModal({
  tenantId,
  environment,
  onClose,
  onSaved,
}: {
  tenantId: string
  environment: EnvironmentResponse | null
  onClose: () => void
  onSaved: () => void
}) {
  const [name, setName] = useState(environment?.name ?? "")
  const [type, setType] = useState<EnvironmentType>(environment?.type ?? "STANDALONE")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (environment) await environmentsApi.update(tenantId, environment.id, { name, type })
      else await environmentsApi.create(tenantId, { name, type })
      onSaved()
    } catch (submitError) {
      setError(submitError)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <form className="fade-in" onSubmit={handleSubmit} style={{
        background: "var(--card)", border: "1px solid var(--border)",
        borderRadius: 16, padding: 28, width: 420, boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
      }}>
        <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 20 }}>
          {environment ? "Edit environment" : "New environment"}
        </h3>

        {error !== null && (
          <div style={{
            display: "flex", gap: 10, padding: "10px 14px", borderRadius: 8, marginBottom: 16,
            background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b", fontSize: 13,
          }}>
            <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{describeError(error)}</span>
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Name</label>
            <input className="input-field" placeholder="DEV" value={name} onChange={e => setName(e.target.value)} maxLength={50} required />
          </div>
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Type</label>
            <select className="input-field" value={type} onChange={e => setType(e.target.value as EnvironmentType)}>
              {ENVIRONMENT_TYPES.map(value => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 24, justifyContent: "flex-end" }}>
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </div>
  )
}
