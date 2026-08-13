import { useState } from "react"
import { Plus, Building2, AlertTriangle } from "lucide-react"
import { tenantsApi } from "../api/tenantsApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState, describeError } from "../components/DataState"
import PermissionGate from "../components/PermissionGate"
import { PERMISSIONS } from "../types"
import type { TenantResponse } from "../types/api"

/**
 * "Clients" in the UI, "tenants" in the API.
 *
 * GET /api/v1/tenants returns only the tenants the caller is a member of, so
 * this list is intentionally scoped rather than global. The backend exposes no
 * update or delete endpoint for tenants, so neither is offered here.
 */
export default function TenantsPage() {
  const tenants = useAsyncData<TenantResponse[]>(() => tenantsApi.list(), [])
  const [creating, setCreating] = useState(false)

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>Clients</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            Clients you are assigned to.
          </p>
        </div>
        <PermissionGate anyOf={[PERMISSIONS.tenantCreate]}>
          <button className="btn-primary" onClick={() => setCreating(true)}>
            <Plus size={14} /> New client
          </button>
        </PermissionGate>
      </div>

      {tenants.loading ? (
        <LoadingState label="Loading clients..." />
      ) : tenants.error !== null ? (
        <ErrorState error={tenants.error} onRetry={tenants.reload} />
      ) : (tenants.data ?? []).length === 0 ? (
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12 }}>
          <EmptyState
            title="No clients assigned"
            description="You are not a member of any client yet. An administrator can create one and add you to it."
          />
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 16 }}>
          {(tenants.data ?? []).map(tenant => (
            <div key={tenant.id} className="metric-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 9,
                  background: "color-mix(in srgb, var(--primary) 12%, transparent)",
                  color: "var(--primary)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <Building2 size={17} />
                </div>
                <span className="badge" style={{
                  background: tenant.active ? "#dcfce7" : "#f3f4f6",
                  color: tenant.active ? "#16a34a" : "#6b7280",
                }}>
                  {tenant.active ? "active" : "inactive"}
                </span>
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em" }}>{tenant.name}</div>
                <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 3 }}>
                  Created {new Date(tenant.createdAt).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {creating && (
        <CreateTenantModal
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false)
            tenants.reload()
          }}
        />
      )}
    </div>
  )
}

function CreateTenantModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await tenantsApi.create({ name })
      onCreated()
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
        <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 4 }}>New client</h3>
        <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginBottom: 20 }}>
          Client names must be unique.
        </p>

        {error !== null && (
          <div style={{
            display: "flex", gap: 10, padding: "10px 14px", borderRadius: 8, marginBottom: 16,
            background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b", fontSize: 13,
          }}>
            <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{describeError(error)}</span>
          </div>
        )}

        <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Name</label>
        <input className="input-field" value={name} onChange={e => setName(e.target.value)} maxLength={160} required />

        <div style={{ display: "flex", gap: 8, marginTop: 24, justifyContent: "flex-end" }}>
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Creating..." : "Create"}
          </button>
        </div>
      </form>
    </div>
  )
}
