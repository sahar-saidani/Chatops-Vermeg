import { useEffect, useState } from "react"
import { Outlet, useLocation, useNavigate } from "react-router-dom"
import Sidebar from "./Sidebar"
import TopBar from "./TopBar"
import { useAuth } from "../context/AuthContext"

const DARK_MODE_KEY = "chatops.darkMode"

/** Route path -> page title, used by TopBar and the breadcrumb. */
export const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/chat": "AI Chat",
  "/users": "User Management",
  "/roles": "Roles",
  "/permissions": "Permissions",
  "/tenants": "Clients",
  "/environments": "Environments",
  "/git": "Git",
  "/jenkins": "Jenkins",
  "/installation": "Installation",
  "/logs": "Logs",
  "/infrastructure": "Infrastructure",
  "/history": "History",
  "/settings": "Settings",
}

export default function AppLayout() {
  const [dark, setDark] = useState(() => window.localStorage.getItem(DARK_MODE_KEY) === "true")
  const { logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
    window.localStorage.setItem(DARK_MODE_KEY, String(dark))
  }, [dark])

  const title = PAGE_TITLES[location.pathname] ?? "ChatOps"
  const breadcrumb = location.pathname === "/dashboard" ? undefined : ["Home", title]

  const handleLogout = () => {
    logout()
    navigate("/login", { replace: true })
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--background)" }}>
      <Sidebar darkMode={dark} onToggleDark={() => setDark(!dark)} onLogout={handleLogout} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <TopBar title={title} breadcrumb={breadcrumb} />
        <main style={{ flex: 1, overflowY: "auto" }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
