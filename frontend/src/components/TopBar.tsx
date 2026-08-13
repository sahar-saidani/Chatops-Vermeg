import { useAuth } from "../context/AuthContext"

interface TopBarProps {
  title: string
  breadcrumb?: string[]
}

export default function TopBar({ title, breadcrumb }: TopBarProps) {
  const { user, roles } = useAuth()

  // The tenant chip reflects the caller's real memberships. A user can belong
  // to several tenants, so this labels the set rather than inventing a
  // "current tenant" the backend has no concept of.
  const activeMemberships = (user?.memberships ?? []).filter((membership) => membership.active)
  const tenantLabel =
    activeMemberships.length === 0
      ? "No client assigned"
      : activeMemberships.length === 1
        ? activeMemberships[0].tenantName
        : `${activeMemberships.length} clients`

  return (
    <header style={{
      height: 56, background: "var(--card)", borderBottom: "1px solid var(--border)",
      display: "flex", alignItems: "center", padding: "0 24px", gap: 16,
      position: "sticky", top: 0, zIndex: 10,
    }}>
      <div style={{ flex: 1 }}>
        {breadcrumb && (
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 1 }}>
            {breadcrumb.map((crumb, i) => (
              <span key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {i > 0 && <span style={{ color: "var(--muted-foreground)", fontSize: 12 }}>/</span>}
                <span style={{ fontSize: 12, color: i === breadcrumb.length - 1 ? "var(--foreground)" : "var(--muted-foreground)", fontWeight: i === breadcrumb.length - 1 ? 600 : 400 }}>
                  {crumb}
                </span>
              </span>
            ))}
          </div>
        )}
        {!breadcrumb && <h1 style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em" }}>{title}</h1>}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {/* Client / tenant membership */}
        <div style={{
          display: "flex", alignItems: "center", gap: 6,
          padding: "6px 12px", borderRadius: 7,
          background: "var(--muted)", border: "1px solid var(--border)",
          fontSize: 12.5, fontWeight: 500, color: "var(--foreground)",
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: "50%",
            background: activeMemberships.length > 0 ? "#16a34a" : "var(--muted-foreground)",
            display: "inline-block",
          }} />
          {tenantLabel}
        </div>

        {/* Roles held by the signed-in user */}
        {roles.length > 0 && (
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "5px 12px", borderRadius: 7,
            background: "color-mix(in srgb, var(--primary) 12%, transparent)",
            border: "1px solid color-mix(in srgb, var(--primary) 30%, transparent)",
          }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)" }}>{roles.join(" · ")}</span>
          </div>
        )}
      </div>
    </header>
  )
}
