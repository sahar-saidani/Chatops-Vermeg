import {
  LayoutDashboard, MessageSquare, Users, Shield, Building2, KeyRound,
  Server, Package, GitBranch, ScrollText, History, Settings, Activity,
  Terminal, Sun, Moon, LogOut, Hammer,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { NavLink } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { PERMISSIONS } from "../types"

interface SidebarProps {
  darkMode: boolean
  onToggleDark: () => void
  onLogout: () => void
}

interface NavItem {
  to: string
  icon: LucideIcon
  label: string
  /** Hidden unless the user holds at least one of these. Absent means always visible. */
  anyPermission?: string[]
}

/**
 * Navigation is derived from the backend's permission codes rather than from a
 * hardcoded role, because roles are database rows and an administrator can
 * define new ones at any time.
 *
 * Oracle, Jira, Grafana, Security, Audit, Business Docs, Reports, Projects and
 * Configuration entries were removed: none of them has a backend behind it.
 * jira-agent still exists server-side and is intentionally not surfaced here.
 */
const NAV_GROUPS: { group: string; items: NavItem[] }[] = [
  {
    group: "Overview",
    items: [
      { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
      { to: "/chat", icon: MessageSquare, label: "AI Chat" },
    ],
  },
  {
    group: "Administration",
    items: [
      { to: "/users", icon: Users, label: "User Management", anyPermission: [PERMISSIONS.userRead] },
      { to: "/roles", icon: Shield, label: "Roles", anyPermission: [PERMISSIONS.roleManage] },
      { to: "/permissions", icon: KeyRound, label: "Permissions", anyPermission: [PERMISSIONS.permissionManage] },
      { to: "/tenants", icon: Building2, label: "Clients" },
      { to: "/environments", icon: Server, label: "Environments", anyPermission: [PERMISSIONS.environmentRead] },
    ],
  },
  {
    group: "Agents",
    items: [
      { to: "/infrastructure", icon: Activity, label: "Infrastructure" },
      { to: "/installation", icon: Package, label: "Installation" },
      { to: "/jenkins", icon: Hammer, label: "Jenkins" },
      { to: "/git", icon: GitBranch, label: "Git" },
      { to: "/logs", icon: ScrollText, label: "Logs" },
    ],
  },
  {
    group: "Account",
    items: [
      { to: "/history", icon: History, label: "History" },
      { to: "/settings", icon: Settings, label: "Settings" },
    ],
  },
]

function initialsOf(displayName: string): string {
  const parts = displayName.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "?"
  return parts.map((part) => part[0]).join("").slice(0, 2).toUpperCase()
}

export default function Sidebar({ darkMode, onToggleDark, onLogout }: SidebarProps) {
  const { user, roles, hasPermission } = useAuth()

  const visibleGroups = NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.anyPermission || hasPermission(...item.anyPermission)),
  })).filter((group) => group.items.length > 0)

  return (
    <aside style={{
      width: 240,
      flexShrink: 0,
      background: "var(--card)",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      position: "sticky",
      top: 0,
      overflowY: "auto",
    }}>
      {/* Logo */}
      <div style={{
        padding: "20px 16px 16px",
        borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9,
          background: "linear-gradient(135deg, #4f46e5, #6366f1)",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 0 16px rgba(99,102,241,0.35)", flexShrink: 0,
        }}>
          <Terminal size={17} color="white" />
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 14, letterSpacing: "-0.01em" }}>ChatOps</div>
          <div style={{ fontWeight: 700, fontSize: 10, color: "#6366f1", letterSpacing: "0.1em", textTransform: "uppercase" }}>Solife</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "8px 8px 4px", overflowY: "auto" }}>
        {visibleGroups.map(group => (
          <div key={group.group} style={{ marginBottom: 4 }}>
            <div style={{
              fontSize: 10, fontWeight: 700, color: "var(--muted-foreground)",
              textTransform: "uppercase", letterSpacing: "0.08em",
              padding: "10px 12px 4px",
            }}>
              {group.group}
            </div>
            {group.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `sidebar-nav-item ${isActive ? "active" : ""}`}
                style={{ width: "100%" }}
              >
                <item.icon size={15} />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ borderTop: "1px solid var(--border)", padding: 12 }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "8px 10px", borderRadius: 8,
          background: "var(--muted)", marginBottom: 8,
        }}>
          <div style={{
            width: 30, height: 30, borderRadius: "50%",
            background: "linear-gradient(135deg, #4f46e5, #6366f199)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "white", fontSize: 12, fontWeight: 700, flexShrink: 0,
          }}>
            {initialsOf(user?.displayName ?? "")}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12.5, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.displayName ?? "Unknown user"}
            </div>
            <div style={{ fontSize: 10.5, color: "var(--muted-foreground)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {roles.length > 0 ? roles.join(", ") : "No role assigned"}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 4 }}>
          <button
            onClick={onToggleDark}
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
              gap: 6, padding: "7px 8px", borderRadius: 7, fontSize: 12,
              background: "none", border: "1px solid var(--border)",
              color: "var(--muted-foreground)", cursor: "pointer", transition: "all 0.15s",
              fontWeight: 500,
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "var(--muted)")}
            onMouseLeave={e => (e.currentTarget.style.background = "none")}
          >
            {darkMode ? <Sun size={13} /> : <Moon size={13} />}
            {darkMode ? "Light" : "Dark"}
          </button>
          <button
            onClick={onLogout}
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
              gap: 6, padding: "7px 8px", borderRadius: 7, fontSize: 12,
              background: "none", border: "1px solid var(--border)",
              color: "var(--muted-foreground)", cursor: "pointer", transition: "all 0.15s",
              fontWeight: 500,
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = "#fee2e2"
              e.currentTarget.style.color = "#dc2626"
              e.currentTarget.style.borderColor = "#fca5a5"
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = "none"
              e.currentTarget.style.color = "var(--muted-foreground)"
              e.currentTarget.style.borderColor = "var(--border)"
            }}
          >
            <LogOut size={13} />
            Logout
          </button>
        </div>
      </div>
    </aside>
  )
}
