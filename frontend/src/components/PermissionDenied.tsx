import { ShieldAlert } from "lucide-react"

interface PermissionDeniedProps {
  required?: string[]
}

/**
 * Shown when the backend refused an action with 403, or when a route's
 * permission guard fails. Kept visually distinct from an empty state on
 * purpose: "you may not see this" and "there is nothing here" are different
 * answers and must never look the same.
 */
export default function PermissionDenied({ required }: PermissionDeniedProps) {
  return (
    <div
      style={{
        padding: 48,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 12,
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: "#fef3c7",
          color: "#d97706",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <ShieldAlert size={22} />
      </div>
      <h2 style={{ fontSize: 17, fontWeight: 800, letterSpacing: "-0.02em" }}>Permission denied</h2>
      <p style={{ fontSize: 13.5, color: "var(--muted-foreground)", maxWidth: 420, lineHeight: 1.6 }}>
        Your account does not have access to this section. Ask an administrator to grant you the
        required permission.
      </p>
      {required && required.length > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "center" }}>
          {required.map((code) => (
            <span key={code} className="badge" style={{ background: "var(--muted)", color: "var(--muted-foreground)" }}>
              {code}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
