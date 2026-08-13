import { useState } from "react"
import { Plus, Pencil, AlertTriangle } from "lucide-react"
import { permissionsApi } from "../api/permissionsApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState, describeError } from "../components/DataState"
import type { PermissionResponse } from "../types/api"

export default function PermissionsPage() {
  const permissions = useAsyncData<PermissionResponse[]>(() => permissionsApi.list(), [])
  const [editing, setEditing] = useState<PermissionResponse | null>(null)
  const [creating, setCreating] = useState(false)

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>Permissions</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            Permission codes checked by the API on every protected endpoint.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setCreating(true)}>
          <Plus size={14} /> New permission
        </button>
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {permissions.loading ? (
          <LoadingState label="Loading permissions..." />
        ) : permissions.error !== null ? (
          <ErrorState error={permissions.error} onRetry={permissions.reload} />
        ) : (permissions.data ?? []).length === 0 ? (
          <EmptyState title="No permissions" description="No permission has been defined yet." />
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th>Permission</th>
                <th>Code</th>
                <th>Description</th>
                <th style={{ width: 80 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(permissions.data ?? []).map(permission => (
                <tr key={permission.id}>
                  <td style={{ fontSize: 13.5, fontWeight: 600 }}>{permission.name}</td>
                  <td style={{ fontFamily: "monospace", fontSize: 12.5 }}>{permission.code}</td>
                  <td style={{ fontSize: 13, color: "var(--muted-foreground)" }}>{permission.description || "—"}</td>
                  <td>
                    {/* No delete: PermissionController exposes GET/POST/PUT only. */}
                    <button
                      title="Edit permission"
                      onClick={() => setEditing(permission)}
                      style={{
                        width: 28, height: 28, borderRadius: 6,
                        border: "1px solid var(--border)", background: "none", cursor: "pointer",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        color: "var(--muted-foreground)",
                      }}
                    >
                      <Pencil size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {(creating || editing) && (
        <PermissionModal
          permission={editing}
          onClose={() => {
            setCreating(false)
            setEditing(null)
          }}
          onSaved={() => {
            setCreating(false)
            setEditing(null)
            permissions.reload()
          }}
        />
      )}
    </div>
  )
}

function PermissionModal({
  permission,
  onClose,
  onSaved,
}: {
  permission: PermissionResponse | null
  onClose: () => void
  onSaved: () => void
}) {
  const [code, setCode] = useState(permission?.code ?? "")
  const [name, setName] = useState(permission?.name ?? "")
  const [description, setDescription] = useState(permission?.description ?? "")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (permission) await permissionsApi.update(permission.id, { name, description })
      else await permissionsApi.create({ code, name, description })
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
        borderRadius: 16, padding: 28, width: 440, boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
      }}>
        <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 20 }}>
          {permission ? "Edit permission" : "New permission"}
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
          {!permission && (
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Code</label>
              <input
                className="input-field"
                placeholder="REPORT_EXPORT"
                value={code}
                onChange={e => setCode(e.target.value)}
                pattern="[A-Za-z0-9_-]+"
                title="Letters, digits, underscores and hyphens only"
                maxLength={100}
                required
              />
            </div>
          )}
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Name</label>
            <input className="input-field" value={name} onChange={e => setName(e.target.value)} maxLength={120} required />
          </div>
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Description</label>
            <input className="input-field" value={description} onChange={e => setDescription(e.target.value)} maxLength={500} />
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
