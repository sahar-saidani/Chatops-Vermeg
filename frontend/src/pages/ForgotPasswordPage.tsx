import { useState } from "react"
import { Terminal, CheckCircle2, AlertTriangle } from "lucide-react"
import { Link } from "react-router-dom"
import { authApi } from "../api/authApi"
import { describeError } from "../components/DataState"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await authApi.forgotPassword({ email })
      setSubmitted(true)
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

        {submitted ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#16a34a" }}>
              <CheckCircle2 size={20} />
              <span style={{ fontSize: 15, fontWeight: 700 }}>Check your email</span>
            </div>
            <p style={{ fontSize: 13.5, color: "var(--muted-foreground)", lineHeight: 1.6 }}>
              If that address belongs to an account, a password reset link is on its way.
            </p>
            <Link to="/login" className="btn-primary" style={{ justifyContent: "center", textDecoration: "none" }}>
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 6 }}>Reset your password</h2>
            <p style={{ color: "var(--muted-foreground)", fontSize: 13.5, marginBottom: 24, lineHeight: 1.6 }}>
              We will email you a link to choose a new password.
            </p>

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
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Email address</label>
                <input
                  type="email"
                  className="input-field"
                  placeholder="you@company.com"
                  value={email}
                  onChange={event => setEmail(event.target.value)}
                  required
                />
              </div>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
                style={{ width: "100%", justifyContent: "center", padding: "11px 24px" }}
              >
                {loading ? "Sending..." : "Send reset link"}
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
