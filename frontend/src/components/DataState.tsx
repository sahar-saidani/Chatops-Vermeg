import { AlertTriangle, Inbox, RefreshCw } from "lucide-react"
import { ApiError } from "../api/apiClient"

/**
 * Shared loading / empty / error surfaces.
 *
 * Empty and error are separate components on purpose. Rendering a failed call
 * as "no data" is the single most misleading thing this UI could do -- an
 * agent that crashed and an agent that ran and found nothing must never look
 * alike.
 */

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div
      style={{
        padding: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 10,
        color: "var(--muted-foreground)",
        fontSize: 13.5,
      }}
    >
      <span
        style={{
          width: 15,
          height: 15,
          border: "2px solid var(--border)",
          borderTopColor: "var(--primary)",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
          display: "inline-block",
        }}
      />
      {label}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div
      style={{
        padding: 40,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: "var(--muted)",
          color: "var(--muted-foreground)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Inbox size={19} />
      </div>
      <div style={{ fontSize: 14, fontWeight: 700 }}>{title}</div>
      {description && (
        <div style={{ fontSize: 13, color: "var(--muted-foreground)", maxWidth: 380, lineHeight: 1.6 }}>
          {description}
        </div>
      )}
    </div>
  )
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return "An unexpected error occurred."
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div
      style={{
        padding: 40,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: "#fee2e2",
          color: "#dc2626",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <AlertTriangle size={19} />
      </div>
      <div style={{ fontSize: 14, fontWeight: 700 }}>Something went wrong</div>
      <div style={{ fontSize: 13, color: "var(--muted-foreground)", maxWidth: 460, lineHeight: 1.6 }}>
        {describeError(error)}
      </div>
      {onRetry && (
        <button className="btn-secondary" onClick={onRetry} style={{ marginTop: 4 }}>
          <RefreshCw size={13} /> Retry
        </button>
      )}
    </div>
  )
}
