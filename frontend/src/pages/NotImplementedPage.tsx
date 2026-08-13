import { Construction } from "lucide-react"

/**
 * Honest placeholder for a route whose backend integration is not wired yet.
 * It deliberately shows nothing that looks like data -- the previous
 * GenericPage filled these routes with convincing fake servers, pipelines and
 * databases, which is worse than showing nothing.
 */
export default function NotImplementedPage({ title, reason }: { title: string; reason: string }) {
  return (
    <div style={{ padding: 24 }}>
      <div style={{
        background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12,
        padding: 48, display: "flex", flexDirection: "column", alignItems: "center",
        gap: 10, textAlign: "center",
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: 11, background: "var(--muted)",
          color: "var(--muted-foreground)", display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <Construction size={20} />
        </div>
        <h2 style={{ fontSize: 17, fontWeight: 800, letterSpacing: "-0.02em" }}>{title}</h2>
        <p style={{ fontSize: 13.5, color: "var(--muted-foreground)", maxWidth: 460, lineHeight: 1.6 }}>
          {reason}
        </p>
      </div>
    </div>
  )
}
