import { useState } from "react"
import { Terminal, CheckCircle2, AlertTriangle } from "lucide-react"
import { Link, useSearchParams } from "react-router-dom"
import { authApi } from "../api/authApi"
import { describeError } from "../components/DataState"
import type { ActivateAccountRequest, ResetPasswordRequest } from "../types/api"

interface CredentialSetupPageProps {
  /**
   * Activation and password reset are the same form against two endpoints;
   * AuthenticationMailServiceImpl links to /activate?token= and
   * /reset-password?token= respectively.
   */
  mode: "activate" | "reset"
}

const COPY = {
  activate: {
    heading: "Activate your account",
    subheading: "Choose a password to finish setting up your ChatOps workspace.",
    action: "Activate account",
    done: "Your account is active. You can sign in now.",
  },
  reset: {
    heading: "Choose a new password",
    subheading: "Enter a new password for your ChatOps account.",
    action: "Reset password",
    done: "Your password has been changed. You can sign in now.",
  },
} as const

export default function CredentialSetupPage({ mode }: CredentialSetupPageProps) {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") ?? ""
  const copy = COPY[mode]

  const [password, setPassword] = useState("")
  const [confirmation, setConfirmation] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [done, setDone] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (password !== confirmation) {
      setError(new Error("The two passwords do not match."))
      return
    }
    setError(null)
    setLoading(true)
    try {
      const request: ActivateAccountRequest & ResetPasswordRequest = { token, password }
      if (mode === "activate") await authApi.activate(request)
      else await authApi.resetPassword(request)
      setDone(true)
    } catch (submitError) {
      setError(submitError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "var(--background)", padding: 24,
    }}>
      <div style={{
        width: "100%", maxWidth: 420, background: "var(--card)",
        border: "1px solid var(--border)", borderRadius: 16, padding: 32,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 9,
            background: "linear-gradient(135deg, #4f46e5, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Terminal size={18} color="white" />
          </div>
          <span style={{ fontWeight: 800, fontSize: 16 }}>ChatOps Solife</span>
        </div>

        {done ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#16a34a" }}>
              <CheckCircle2 size={20} />
              <span style={{ fontSize: 15, fontWeight: 700 }}>All set</span>
            </div>
            <p style={{ fontSize: 13.5, color: "var(--muted-foreground)", lineHeight: 1.6 }}>{copy.done}</p>
            <Link to="/login" className="btn-primary" style={{ justifyContent: "center", textDecoration: "none" }}>
              Go to sign in
            </Link>
          </div>
        ) : (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 6 }}>{copy.heading}</h2>
            <p style={{ color: "var(--muted-foreground)", fontSize: 13.5, marginBottom: 24, lineHeight: 1.6 }}>
              {copy.subheading}
            </p>

            {!token && (
              <div style={{
                display: "flex", gap: 10, padding: "10px 14px", borderRadius: 8, marginBottom: 18,
                background: "#fef3c7", border: "1px solid #fcd34d", color: "#92400e", fontSize: 13, lineHeight: 1.5,
              }}>
                <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
                <span>This link is missing its token. Use the full link from your email.</span>
              </div>
            )}

            {error !== null && (
              <div style={{
                display: "flex", gap: 10, padding: "10px 14px", borderRadius: 8, marginBottom: 18,
                background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b", fontSize: 13, lineHeight: 1.5,
              }}>
                <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
                <span>{describeError(error)}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>New password</label>
                <input
                  type="password"
                  className="input-field"
                  value={password}
                  onChange={event => setPassword(event.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Confirm password</label>
                <input
                  type="password"
                  className="input-field"
                  value={confirmation}
                  onChange={event => setConfirmation(event.target.value)}
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading || !token}
                style={{ width: "100%", justifyContent: "center", padding: "11px 24px" }}
              >
                {loading ? "Working..." : copy.action}
              </button>
            </form>

            <p style={{ marginTop: 22, fontSize: 12.5, color: "var(--muted-foreground)", textAlign: "center" }}>
              <Link to="/login" style={{ color: "var(--primary)", textDecoration: "none" }}>Back to sign in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
