import { useState } from "react"
import { Check, AlertTriangle, Info } from "lucide-react"
import { usersApi } from "../api/usersApi"
import { useAuth } from "../context/AuthContext"
import { describeError } from "../components/DataState"

/**
 * Only the profile section is wired, because the user endpoint is the only
 * settings-shaped backend that exists: UserUpdateRequest carries displayName
 * and active, and nothing else. Notification, theme-sync and API-key sections
 * are deliberately not faked.
 */
/**
 * Settings the spec asks for that this backend cannot support today. Each is
 * shown with the reason rather than hidden, so the absence is legible.
 */
const UNSUPPORTED_SECTIONS: { title: string; state: string; reason: string }[] = [
  {
    title: "Appearance",
    state: "Available in the sidebar",
    reason:
      "Light and dark mode are switched from the sidebar and stored in this browser. There is no server-side theme preference to sync.",
  },
  {
    title: "Notifications",
    state: "Not available",
    reason:
      "No notification entity, preference table or delivery channel exists in the backend. The only outgoing mail is account activation and password reset.",
  },
  {
    title: "Language",
    state: "Not available",
    reason: "The application ships a single locale; no translation catalogue or locale preference is stored.",
  },
  {
    title: "Security",
    state: "Partly available",
    reason:
      "Passwords are changed through the reset link sent by email. There is no change-password endpoint for a signed-in user, and no multi-factor support.",
  },
  {
    title: "Active sessions",
    state: "Not available",
    reason:
      "Authentication is stateless: the API issues JWTs and keeps no session registry, so there is nothing to list or revoke individually.",
  },
]

export default function SettingsPage() {
  const { user, refreshUser } = useAuth()
  const [displayName, setDisplayName] = useState(user?.displayName ?? "")
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const canEditProfile = user !== null

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!user) return
    setError(null)
    setSaving(true)
    try {
      // Requires USER_WRITE server-side; a user without it gets a 403 shown below.
      await usersApi.update(user.id, { displayName })
      await refreshUser()
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (saveError) {
      setError(saveError)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20, maxWidth: 720 }}>
      <div>
        <h2 style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-0.02em" }}>Settings</h2>
        <p style={{ fontSize: 13, color: "var(--muted-foreground)", marginTop: 2 }}>
          Your account details.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{
        background: "var(--card)", border: "1px solid var(--border)",
        borderRadius: 12, padding: 24, display: "flex", flexDirection: "column", gap: 16,
      }}>
        <h3 style={{ fontSize: 15, fontWeight: 700 }}>Profile</h3>

        {error !== null && (
          <div style={{
            display: "flex", gap: 10, padding: "10px 14px", borderRadius: 8,
            background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b", fontSize: 13,
          }}>
            <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{describeError(error)}</span>
          </div>
        )}

        <div>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Display name</label>
          <input
            className="input-field"
            value={displayName}
            onChange={event => setDisplayName(event.target.value)}
            maxLength={160}
            disabled={!canEditProfile}
            required
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Email address</label>
          <input className="input-field" value={user?.email ?? ""} disabled readOnly />
          <p style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 5 }}>
            The email address identifies your account and cannot be changed here.
          </p>
        </div>

        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Roles</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {(user?.roles ?? []).length === 0
                ? <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>None</span>
                : (user?.roles ?? []).map(role => (
                    <span key={role} className="badge" style={{ background: "var(--muted)", color: "var(--muted-foreground)" }}>{role}</span>
                  ))}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Clients</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {(user?.memberships ?? []).filter(m => m.active).length === 0
                ? <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>None</span>
                : (user?.memberships ?? []).filter(m => m.active).map(membership => (
                    <span key={membership.tenantId} className="badge" style={{ background: "var(--muted)", color: "var(--muted-foreground)" }}>
                      {membership.tenantName}
                    </span>
                  ))}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button type="submit" className="btn-primary" disabled={saving || !canEditProfile}>
            {saving ? "Saving..." : "Save changes"}
          </button>
          {saved && (
            <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#16a34a", fontWeight: 600 }}>
              <Check size={14} /> Saved
            </span>
          )}
        </div>
      </form>

      <div style={{
        background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12,
        padding: 20, display: "flex", gap: 10, alignItems: "flex-start",
      }}>
        <Info size={16} style={{ color: "var(--muted-foreground)", flexShrink: 0, marginTop: 1 }} />
        <div style={{ fontSize: 13, color: "var(--muted-foreground)", lineHeight: 1.6 }}>
          Permissions are granted through roles. To change what you can access, ask an administrator
          to adjust your role assignments under Roles.
        </div>
      </div>

      {/*
        Listed rather than omitted: a settings page that silently lacks these
        sections reads as unfinished, while a section wired to nothing would be
        worse. Each states plainly why it is unavailable, so the gap is a
        documented fact instead of a missing feature.
      */}
      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700 }}>Other settings</h3>
        </div>
        {UNSUPPORTED_SECTIONS.map(section => (
          <div
            key={section.title}
            style={{
              padding: "14px 20px", borderBottom: "1px solid var(--border)",
              display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16,
            }}
          >
            <div>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>{section.title}</div>
              <div style={{ fontSize: 12.5, color: "var(--muted-foreground)", marginTop: 3, lineHeight: 1.55, maxWidth: 520 }}>
                {section.reason}
              </div>
            </div>
            <span className="badge" style={{ background: "var(--muted)", color: "var(--muted-foreground)", flexShrink: 0, whiteSpace: "nowrap" }}>
              {section.state}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
