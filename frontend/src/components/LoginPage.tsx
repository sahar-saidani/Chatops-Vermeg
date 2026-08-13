import { useState } from "react"
import { Terminal, Zap, Shield, Activity, ChevronRight, Eye, EyeOff, AlertTriangle } from "lucide-react"
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { describeError } from "./DataState"

interface LoginLocationState {
  from?: string
}

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPass, setShowPass] = useState(false)
  const [remember, setRemember] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const { login, isAuthenticated, isInitializing } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = (location.state as LoginLocationState | null)?.from ?? "/dashboard"

  if (!isInitializing && isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      // Real POST /api/v1/auth/login. The role the user gets is whatever the
      // backend's RBAC tables say -- it is never inferred from the address.
      await login(email, password, remember)
      navigate(redirectTo, { replace: true })
    } catch (loginError) {
      setError(loginError)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--background)" }}>
      {/* Left panel */}
      <div style={{
        flex: "1",
        background: "linear-gradient(135deg, #0f0f23 0%, #1a1040 40%, #0f172a 100%)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "60px",
        position: "relative",
        overflow: "hidden",
      }} className="hidden md:flex">
        {/* Grid overlay */}
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: "linear-gradient(rgba(99,102,241,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.06) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }} />
        {/* Glow */}
        <div style={{
          position: "absolute", top: "20%", left: "30%",
          width: 400, height: 400,
          background: "radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)",
          borderRadius: "50%", filter: "blur(40px)",
        }} />

        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 64 }}>
            <div style={{
              width: 40, height: 40,
              background: "linear-gradient(135deg, #4f46e5, #6366f1)",
              borderRadius: 10,
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: "0 0 24px rgba(99,102,241,0.5)",
            }}>
              <Terminal size={20} color="white" />
            </div>
            <div>
              <div style={{ color: "white", fontWeight: 800, fontSize: 18, letterSpacing: "-0.02em" }}>ChatOps</div>
              <div style={{ color: "#6366f1", fontWeight: 700, fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase" }}>Solife</div>
            </div>
          </div>

          <h1 style={{
            color: "white", fontSize: 42, fontWeight: 800, lineHeight: 1.15,
            letterSpacing: "-0.03em", marginBottom: 20, maxWidth: 480,
          }}>
            AI-powered DevOps<br />
            <span style={{ color: "#6366f1" }}>intelligence</span> platform
          </h1>
          <p style={{ color: "#94a3b8", fontSize: 16, lineHeight: 1.7, maxWidth: 420, marginBottom: 48 }}>
            Centralize infrastructure, CI/CD, monitoring, and business information through a single AI-powered conversational interface.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {[
              { icon: <Zap size={16} />, text: "Real-time infrastructure monitoring & alerts" },
              { icon: <Shield size={16} />, text: "Enterprise-grade security & audit logging" },
              { icon: <Activity size={16} />, text: "AI-driven insights across all systems" },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: "rgba(99,102,241,0.15)",
                  border: "1px solid rgba(99,102,241,0.3)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#6366f1",
                }}>
                  {item.icon}
                </div>
                <span style={{ color: "#cbd5e1", fontSize: 14 }}>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div style={{
        width: "100%", maxWidth: 460,
        display: "flex", flexDirection: "column", justifyContent: "center",
        padding: "40px 48px",
        background: "var(--card)",
        borderLeft: "1px solid var(--border)",
      }}>
        {/* Mobile logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 40 }} className="md:hidden">
          <div style={{
            width: 36, height: 36, borderRadius: 9,
            background: "linear-gradient(135deg, #4f46e5, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Terminal size={18} color="white" />
          </div>
          <span style={{ fontWeight: 800, fontSize: 16 }}>ChatOps Solife</span>
        </div>

        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 6 }}>Welcome back</h2>
          <p style={{ color: "var(--muted-foreground)", fontSize: 14 }}>Sign in to your workspace</p>
        </div>

        {error !== null && (
          <div style={{
            display: "flex", alignItems: "flex-start", gap: 10,
            padding: "10px 14px", borderRadius: 8, marginBottom: 18,
            background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b",
            fontSize: 13, lineHeight: 1.5,
          }}>
            <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{describeError(error)}</span>
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 6, color: "var(--foreground)" }}>
              Email address
            </label>
            <input
              type="email"
              className="input-field"
              placeholder="you@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <label style={{ fontSize: 13, fontWeight: 600 }}>Password</label>
              <Link to="/forgot-password" style={{ fontSize: 12, color: "var(--primary)", fontWeight: 500, textDecoration: "none" }}>
                Forgot password?
              </Link>
            </div>
            <div style={{ position: "relative" }}>
              <input
                type={showPass ? "text" : "password"}
                className="input-field"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ paddingRight: 44 }}
                required
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                style={{
                  position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", cursor: "pointer", color: "var(--muted-foreground)",
                }}
              >
                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              id="remember"
              checked={remember}
              onChange={e => setRemember(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: "var(--primary)", cursor: "pointer" }}
            />
            <label htmlFor="remember" style={{ fontSize: 13, color: "var(--muted-foreground)", cursor: "pointer" }}>
              Keep me signed in on this browser
            </label>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: "100%", justifyContent: "center", padding: "12px 24px", fontSize: 15, marginTop: 4 }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{
                  width: 16, height: 16, border: "2px solid rgba(255,255,255,0.3)",
                  borderTopColor: "white", borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }} />
                Authenticating...
              </span>
            ) : (
              <>Sign in <ChevronRight size={16} /></>
            )}
          </button>
        </form>

        <p style={{ marginTop: 28, fontSize: 12, color: "var(--muted-foreground)", textAlign: "center", lineHeight: 1.6 }}>
          Accounts are created by invitation. Ask an administrator to invite you, then use the
          activation link from your email.
        </p>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
