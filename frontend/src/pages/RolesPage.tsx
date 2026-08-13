import { useState } from "react"
import { Plus, Pencil, Trash2, AlertTriangle, Lock, Shield, Grid3x3, Check, Minus } from "lucide-react"
import { rolesApi } from "../api/rolesApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState, describeError } from "../components/DataState"
import type { RoleResponse } from "../types/api"

type RolesView = "list" | "matrix"

export default function RolesPage() {
  const roles = useAsyncData<RoleResponse[]>(() => rolesApi.list(), [])
  const [editing, setEditing] = useState<RoleResponse | null>(null)
  const [creating, setCreating] = useState(false)
  const [actionError, setActionError] = useState<unknown>(null)
  const [view, setView] = useState<RolesView>("list")

  const remove = async (role: RoleResponse) => {
    setActionError(null)
    try {
      await rolesApi.remove(role.id)
      roles.reload()
    } catch (error) {
      setActionError(error)
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>Roles</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            Roles grant permissions to users within a client.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ display: "flex", gap: 4, background: "var(--muted)", padding: 3, borderRadius: 8, border: "1px solid var(--border)" }}>
            {(["list", "matrix"] as RolesView[]).map(candidate => (
              <button
                key={candidate}
                onClick={() => setView(candidate)}
                style={{
                  display: "flex", alignItems: "center", gap: 6,
                  padding: "5px 12px", borderRadius: 6, fontSize: 12.5, fontWeight: 600,
                  border: "none", cursor: "pointer",
                  background: view === candidate ? "var(--card)" : "transparent",
                  color: view === candidate ? "var(--foreground)" : "var(--muted-foreground)",
                }}
              >
                {candidate === "list" ? <Shield size={13} /> : <Grid3x3 size={13} />}
                {candidate === "list" ? "Roles" : "Permission matrix"}
              </button>
            ))}
          </div>
          <button className="btn-primary" onClick={() => setCreating(true)}>
            <Plus size={14} /> New role
          </button>
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

      {view === "matrix" && <PermissionMatrix />}

      <div style={{ display: view === "list" ? "block" : "none", background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {roles.loading ? (
          <LoadingState label="Loading roles..." />
        ) : roles.error !== null ? (
          <ErrorState error={roles.error} onRetry={roles.reload} />
        ) : (roles.data ?? []).length === 0 ? (
          <EmptyState title="No roles" description="Create a role to start granting permissions." />
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th>Role</th>
                <th>Code</th>
                <th>Description</th>
                <th style={{ width: 110 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(roles.data ?? []).map(role => (
                <tr key={role.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 13.5, fontWeight: 600 }}>{role.name}</span>
                      {role.system && (
                        <span className="badge" style={{ background: "var(--muted)", color: "var(--muted-foreground)", gap: 4 }}>
                          <Lock size={9} /> system
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: 12.5 }}>{role.code}</td>
                  <td style={{ fontSize: 13, color: "var(--muted-foreground)" }}>{role.description || "—"}</td>
                  <td>
                    <div style={{ display: "flex", gap: 4 }}>
                      <button
                        title="Edit role"
                        onClick={() => setEditing(role)}
                        style={iconButtonStyle("var(--muted-foreground)")}
                      >
                        <Pencil size={13} />
                      </button>
                      {/* System roles are protected server-side (SystemRoleProtectedException), so no delete offered. */}
                      {!role.system && (
                        <button
                          title="Delete role"
                          onClick={() => remove(role)}
                          style={iconButtonStyle("#dc2626")}
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {(creating || editing) && (
        <RoleModal
          role={editing}
          onClose={() => {
            setCreating(false)
            setEditing(null)
          }}
          onSaved={() => {
            setCreating(false)
            setEditing(null)
            roles.reload()
          }}
        />
      )}
    </div>
  )
}

/**
 * Roles x permissions grid from GET /api/v1/roles/permission-matrix.
 *
 * Read-only, because the backend exposes no way to grant or revoke a
 * permission -- role_permissions rows come from the Flyway seeds. Rendering
 * checkboxes here would imply an edit the API cannot perform.
 */
function PermissionMatrix() {
  const matrix = useAsyncData(() => rolesApi.permissionMatrix(), [])

  if (matrix.loading) return <LoadingState label="Loading permission matrix..." />
  if (matrix.error !== null) return <ErrorState error={matrix.error} onRetry={matrix.reload} />

  const data = matrix.data
  if (!data || data.roles.length === 0 || data.permissions.length === 0) {
    return (
      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12 }}>
        <EmptyState title="Nothing to show" description="No role or permission has been defined yet." />
      </div>
    )
  }

  return (
    <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
      <div style={{ padding: "12px 18px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <span style={{ fontSize: 12.5, color: "var(--muted-foreground)" }}>
          {data.roles.length} roles × {data.permissions.length} permissions
        </span>
        <span className="badge" style={{ background: "var(--muted)", color: "var(--muted-foreground)" }}>
          read-only
        </span>
      </div>

      {/* The grid can exceed the viewport, so it scrolls inside its own box. */}
      <div style={{ overflowX: "auto" }}>
        <table className="table-container" style={{ minWidth: 640 }}>
          <thead>
            <tr>
              <th style={{ position: "sticky", left: 0, background: "var(--muted)", zIndex: 1 }}>Permission</th>
              {data.roles.map(role => (
                <th key={role.id} style={{ textAlign: "center", whiteSpace: "nowrap" }}>{role.code}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.permissions.map(permission => (
              <tr key={permission.id}>
                <td style={{ position: "sticky", left: 0, background: "var(--card)", fontFamily: "monospace", fontSize: 12.5, whiteSpace: "nowrap" }}>
                  {permission.code}
                </td>
                {data.roles.map(role => {
                  const granted = role.permissionCodes.includes(permission.code)
                  return (
                    <td key={role.id} style={{ textAlign: "center" }}>
                      {granted ? (
                        <Check size={15} color="#16a34a" aria-label={`${role.code} has ${permission.code}`} />
                      ) : (
                        <Minus size={15} color="var(--muted-foreground)" aria-label={`${role.code} lacks ${permission.code}`} />
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function iconButtonStyle(color: string): React.CSSProperties {
  return {
    width: 28, height: 28, borderRadius: 6,
    border: "1px solid var(--border)", background: "none",
    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
    color,
  }
}

function RoleModal({ role, onClose, onSaved }: { role: RoleResponse | null; onClose: () => void; onSaved: () => void }) {
  const [code, setCode] = useState(role?.code ?? "")
  const [name, setName] = useState(role?.name ?? "")
  const [description, setDescription] = useState(role?.description ?? "")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      // RoleUpdateRequest has no code field: a role's code is immutable once created.
      if (role) await rolesApi.update(role.id, { name, description })
      else await rolesApi.create({ code, name, description })
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
        <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 20 }}>{role ? "Edit role" : "New role"}</h3>

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
          {!role && (
            <div>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Code</label>
              <input
                className="input-field"
                placeholder="SUPPORT_ENGINEER"
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
