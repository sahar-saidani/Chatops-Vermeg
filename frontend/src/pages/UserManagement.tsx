import { useMemo, useState } from "react"
import { Search, Plus, UserX, UserCheck, Copy, Check, AlertTriangle } from "lucide-react"
import { usersApi } from "../api/usersApi"
import { rolesApi } from "../api/rolesApi"
import { tenantsApi } from "../api/tenantsApi"
import { authApi } from "../api/authApi"
import { useAsyncData } from "../hooks/useAsyncData"
import { EmptyState, ErrorState, LoadingState, describeError } from "../components/DataState"
import PermissionGate from "../components/PermissionGate"
import { PERMISSIONS } from "../types"
import type { UserResponse, UserStatus } from "../types/api"

const STATUS_BADGE: Record<UserStatus, { bg: string; color: string; label: string }> = {
  ACTIVE: { bg: "#dcfce7", color: "#16a34a", label: "active" },
  PENDING_ACTIVATION: { bg: "#fef3c7", color: "#d97706", label: "pending" },
  LOCKED: { bg: "#fee2e2", color: "#dc2626", label: "locked" },
  DISABLED: { bg: "#f3f4f6", color: "#6b7280", label: "disabled" },
}

function initialsOf(displayName: string): string {
  const parts = displayName.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "?"
  return parts.map((part) => part[0]).join("").slice(0, 2).toUpperCase()
}

export default function UserManagement() {
  const [search, setSearch] = useState("")
  const [showInvite, setShowInvite] = useState(false)
  const [actionError, setActionError] = useState<unknown>(null)

  const users = useAsyncData<UserResponse[]>(() => usersApi.list(), [])

  const filtered = useMemo(() => {
    const list = users.data ?? []
    const needle = search.trim().toLowerCase()
    if (!needle) return list
    return list.filter(
      (user) =>
        user.displayName.toLowerCase().includes(needle) || user.email.toLowerCase().includes(needle),
    )
  }, [users.data, search])

  const setActive = async (user: UserResponse, active: boolean) => {
    setActionError(null)
    try {
      await usersApi.update(user.id, { active })
      users.reload()
    } catch (error) {
      setActionError(error)
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>User Management</h2>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
            {users.data ? `${users.data.length} user${users.data.length === 1 ? "" : "s"}` : "Loading users..."}
          </p>
        </div>
        <PermissionGate anyOf={[PERMISSIONS.userWrite]}>
          <button className="btn-primary" onClick={() => setShowInvite(true)}>
            <Plus size={14} /> Invite User
          </button>
        </PermissionGate>
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

      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ position: "relative", flex: 1, maxWidth: 320 }}>
          <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
          <input
            className="input-field"
            placeholder="Search users..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: 36 }}
          />
        </div>
      </div>

      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        {users.loading ? (
          <LoadingState label="Loading users..." />
        ) : users.error !== null ? (
          <ErrorState error={users.error} onRetry={users.reload} />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={search ? "No matching users" : "No users yet"}
            description={
              search
                ? "No user matches your search."
                : "Users are created by invitation. Use Invite User to add the first one."
            }
          />
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th>User</th>
                <th>Clients</th>
                <th>Status</th>
                <th>Created</th>
                <th style={{ width: 120 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(user => {
                const badge = STATUS_BADGE[user.status]
                const activeMemberships = user.memberships.filter(membership => membership.active)
                return (
                  <tr key={user.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: "50%",
                          background: "linear-gradient(135deg, #4f46e560, #6366f130)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 11, fontWeight: 700, color: "#4f46e5", flexShrink: 0,
                        }}>
                          {initialsOf(user.displayName)}
                        </div>
                        <div>
                          <div style={{ fontSize: 13.5, fontWeight: 600 }}>{user.displayName}</div>
                          <div style={{ fontSize: 12, color: "var(--muted-foreground)" }}>{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ fontSize: 13 }}>
                      {activeMemberships.length === 0
                        ? <span style={{ color: "var(--muted-foreground)" }}>None</span>
                        : activeMemberships.map(membership => membership.tenantName).join(", ")}
                    </td>
                    <td>
                      <span className="badge" style={{ background: badge.bg, color: badge.color }}>
                        <span style={{ width: 5, height: 5, borderRadius: "50%", background: badge.color, display: "inline-block", marginRight: 5 }} />
                        {badge.label}
                      </span>
                    </td>
                    <td style={{ fontSize: 13, color: "var(--muted-foreground)" }}>
                      {new Date(user.createdAt).toLocaleDateString()}
                    </td>
                    <td>
                      <PermissionGate anyOf={[PERMISSIONS.userWrite]}>
                        {user.status === "ACTIVE" ? (
                          <button
                            className="btn-secondary"
                            style={{ fontSize: 12, padding: "5px 10px" }}
                            onClick={() => setActive(user, false)}
                          >
                            <UserX size={12} /> Disable
                          </button>
                        ) : (
                          <button
                            className="btn-secondary"
                            style={{ fontSize: 12, padding: "5px 10px" }}
                            onClick={() => setActive(user, true)}
                          >
                            <UserCheck size={12} /> Enable
                          </button>
                        )}
                      </PermissionGate>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {showInvite && (
        <InviteUserModal
          onClose={() => setShowInvite(false)}
          onInvited={() => {
            setShowInvite(false)
            users.reload()
          }}
        />
      )}
    </div>
  )
}

/**
 * POST /api/v1/auth/invitations takes a tenantId and a list of roleIds, so the
 * form loads the real tenants and roles rather than offering a fixed list.
 * The response is a one-time activation token: the backend also mails it, but
 * showing it here keeps the flow usable when no SMTP server is configured.
 */
function InviteUserModal({ onClose, onInvited }: { onClose: () => void; onInvited: () => void }) {
  const roles = useAsyncData(() => rolesApi.list(), [])
  const tenants = useAsyncData(() => tenantsApi.list(), [])

  const [email, setEmail] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [tenantId, setTenantId] = useState("")
  const [roleIds, setRoleIds] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [activationToken, setActivationToken] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const activationLink = activationToken
    ? `${window.location.origin}/activate?token=${encodeURIComponent(activationToken)}`
    : null

  const toggleRole = (id: string) =>
    setRoleIds(current => (current.includes(id) ? current.filter(value => value !== id) : [...current, id]))

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const response = await authApi.invite({ email, displayName, tenantId, roleIds })
      setActivationToken(response.token)
    } catch (submitError) {
      setError(submitError)
    } finally {
      setSubmitting(false)
    }
  }

  const copyLink = async () => {
    if (!activationLink) return
    await navigator.clipboard.writeText(activationLink)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="fade-in" style={{
        background: "var(--card)", border: "1px solid var(--border)",
        borderRadius: 16, padding: 28, width: 460, maxHeight: "88vh", overflowY: "auto",
        boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
      }}>
        {activationToken ? (
          <>
            <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 4 }}>Invitation created</h3>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginBottom: 18, lineHeight: 1.6 }}>
              An activation email was sent to {email}. If mail delivery is not configured in this
              environment, share this one-time link instead.
            </p>
            <div style={{
              padding: 12, borderRadius: 8, background: "var(--muted)", border: "1px solid var(--border)",
              fontSize: 12, wordBreak: "break-all", fontFamily: "monospace", marginBottom: 12,
            }}>
              {activationLink}
            </div>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button className="btn-secondary" onClick={copyLink}>
                {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? "Copied" : "Copy link"}
              </button>
              <button className="btn-primary" onClick={onInvited}>Done</button>
            </div>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 4 }}>Invite New User</h3>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginBottom: 20 }}>
              The user receives an email with an activation link.
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

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Display name</label>
                <input className="input-field" placeholder="Jane Doe" value={displayName} onChange={e => setDisplayName(e.target.value)} required />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Email address</label>
                <input type="email" className="input-field" placeholder="jane@company.com" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Client</label>
                {tenants.loading ? (
                  <div style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Loading clients...</div>
                ) : tenants.error !== null ? (
                  <div style={{ fontSize: 13, color: "#dc2626" }}>{describeError(tenants.error)}</div>
                ) : (tenants.data ?? []).length === 0 ? (
                  <div style={{ fontSize: 13, color: "var(--muted-foreground)" }}>
                    No client available. Create one under Clients first.
                  </div>
                ) : (
                  <select className="input-field" value={tenantId} onChange={e => setTenantId(e.target.value)} required>
                    <option value="">Select a client...</option>
                    {(tenants.data ?? []).map(tenant => (
                      <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                    ))}
                  </select>
                )}
              </div>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Roles</label>
                {roles.loading ? (
                  <div style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Loading roles...</div>
                ) : roles.error !== null ? (
                  <div style={{ fontSize: 13, color: "#dc2626" }}>{describeError(roles.error)}</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {(roles.data ?? []).map(role => (
                      <label key={role.id} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={roleIds.includes(role.id)}
                          onChange={() => toggleRole(role.id)}
                          style={{ width: 15, height: 15, accentColor: "var(--primary)", cursor: "pointer" }}
                        />
                        <span style={{ fontWeight: 600 }}>{role.name}</span>
                        <span style={{ color: "var(--muted-foreground)", fontSize: 12 }}>{role.code}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 24, justifyContent: "flex-end" }}>
              <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={submitting || roleIds.length === 0 || !tenantId}>
                <Plus size={14} /> {submitting ? "Sending..." : "Send Invitation"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
