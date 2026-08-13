import type { ReactNode } from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import PermissionDenied from "./PermissionDenied"

interface ProtectedRouteProps {
  children: ReactNode
  /** Permission codes; the user needs at least one of them. Omit to require only a session. */
  anyPermission?: string[]
}

export default function ProtectedRoute({ children, anyPermission }: ProtectedRouteProps) {
  const { isAuthenticated, isInitializing, hasPermission } = useAuth()
  const location = useLocation()

  // Without this gate a refresh on a deep link would flash the login page
  // before the stored token has been validated.
  if (isInitializing) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--background)",
          color: "var(--muted-foreground)",
          fontSize: 14,
        }}
      >
        Restoring your session...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }

  if (anyPermission && anyPermission.length > 0 && !hasPermission(...anyPermission)) {
    return <PermissionDenied required={anyPermission} />
  }

  return <>{children}</>
}
