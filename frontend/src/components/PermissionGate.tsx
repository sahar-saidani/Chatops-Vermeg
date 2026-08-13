import type { ReactNode } from "react"
import { useAuth } from "../context/AuthContext"

interface PermissionGateProps {
  /** The user needs at least one of these permission codes. */
  anyOf: string[]
  children: ReactNode
  /** Rendered instead of children when the check fails. Defaults to nothing. */
  fallback?: ReactNode
}

/**
 * Hides a piece of UI the user cannot act on (an "Invite" button, a delete
 * icon). This is a usability guard only -- the backend's @PreAuthorize checks
 * remain the actual enforcement.
 */
export default function PermissionGate({ anyOf, children, fallback = null }: PermissionGateProps) {
  const { hasPermission } = useAuth()
  return <>{hasPermission(...anyOf) ? children : fallback}</>
}
