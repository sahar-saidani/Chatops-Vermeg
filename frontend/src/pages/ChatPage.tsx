import { useEffect, useRef, useState } from "react"
import {
  Send, Sparkles, Copy, Check, AlertTriangle, GitBranch, Hammer,
  Package, ScrollText, Activity, Bot, User as UserIcon, CloudOff,
} from "lucide-react"
import { chatApi } from "../api/chatApi"
import type { ChatResponse } from "../api/chatApi"
import { useAuth } from "../context/AuthContext"
import { describeError } from "../components/DataState"
import { AGENT_LABELS } from "../types"
import type { AgentKey } from "../types"

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  /** Present on assistant turns so the UI can show what actually ran. */
  meta?: ChatResponse
  /** Set when the request itself failed, which is distinct from an empty answer. */
  failed?: boolean
}

/** Only the five agents this UI surfaces. jira-agent is deliberately absent. */
const SUGGESTIONS: { icon: React.ReactNode; agent: AgentKey; text: string }[] = [
  { icon: <GitBranch size={14} />, agent: "git", text: "What changed in the repository recently?" },
  { icon: <Hammer size={14} />, agent: "jenkins", text: "Show me the latest Jenkins build results" },
  { icon: <Package size={14} />, agent: "installation", text: "What version is installed on the DEV machine?" },
  { icon: <ScrollText size={14} />, agent: "log", text: "Are there any errors in the recent logs?" },
  { icon: <Activity size={14} />, agent: "infrastructure", text: "How is the server health right now?" },
]

/**
 * Minimal inline markdown: bold, inline code, and fenced code blocks. A full
 * markdown dependency is not warranted for what the orchestrator's analyzer
 * actually emits, and keeping it inline avoids shipping an HTML sanitizer.
 */
function renderInline(text: string, keyPrefix: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, index) => {
    const key = `${keyPrefix}-${index}`
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={key}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code key={key} style={{
          fontFamily: "monospace", fontSize: 12.5, background: "var(--muted)",
          padding: "1px 5px", borderRadius: 4,
        }}>
          {part.slice(1, -1)}
        </code>
      )
    }
    return <span key={key}>{part}</span>
  })
}

function MarkdownText({ text }: { text: string }) {
  const blocks: React.ReactNode[] = []
  const lines = text.split("\n")
  let codeBuffer: string[] | null = null

  lines.forEach((line, index) => {
    if (line.trimStart().startsWith("```")) {
      if (codeBuffer === null) {
        codeBuffer = []
      } else {
        blocks.push(
          <pre key={`code-${index}`} style={{
            background: "var(--muted)", border: "1px solid var(--border)", borderRadius: 8,
            padding: "10px 12px", fontSize: 12.5, fontFamily: "monospace",
            overflowX: "auto", margin: "6px 0", whiteSpace: "pre",
          }}>
            {codeBuffer.join("\n")}
          </pre>,
        )
        codeBuffer = null
      }
      return
    }
    if (codeBuffer !== null) {
      codeBuffer.push(line)
      return
    }
    if (line.trim() === "") {
      blocks.push(<div key={`sp-${index}`} style={{ height: 6 }} />)
      return
    }
    if (/^\s*[-*]\s+/.test(line)) {
      blocks.push(
        <div key={`li-${index}`} style={{ paddingLeft: 14, display: "flex", gap: 6 }}>
          <span>•</span>
          <span>{renderInline(line.replace(/^\s*[-*]\s+/, ""), `li-${index}`)}</span>
        </div>,
      )
      return
    }
    blocks.push(<div key={`p-${index}`}>{renderInline(line, `p-${index}`)}</div>)
  })

  if (codeBuffer !== null) {
    blocks.push(
      <pre key="code-tail" style={{
        background: "var(--muted)", border: "1px solid var(--border)", borderRadius: 8,
        padding: "10px 12px", fontSize: 12.5, fontFamily: "monospace",
        overflowX: "auto", margin: "6px 0", whiteSpace: "pre",
      }}>
        {(codeBuffer as string[]).join("\n")}
      </pre>,
    )
  }

  return <>{blocks}</>
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: 4, padding: "4px 0" }}>
      {[0, 1, 2].map(i => (
        <div key={i} className="typing-dot" style={{
          width: 7, height: 7, borderRadius: "50%", background: "var(--muted-foreground)",
          animationDelay: `${i * 0.2}s`,
        }} />
      ))}
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"
  const [copied, setCopied] = useState(false)

  const copyText = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="fade-in" style={{
      display: "flex", flexDirection: isUser ? "row-reverse" : "row",
      gap: 10, alignItems: "flex-start",
    }}>
      <div style={{
        width: 30, height: 30, borderRadius: 8, flexShrink: 0,
        background: isUser ? "var(--muted)" : "color-mix(in srgb, var(--primary) 14%, transparent)",
        color: isUser ? "var(--muted-foreground)" : "var(--primary)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {isUser ? <UserIcon size={15} /> : <Bot size={15} />}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: "80%", alignItems: isUser ? "flex-end" : "flex-start" }}>
        <div
          className={isUser ? "chat-bubble-user" : "chat-bubble-ai"}
          style={
            message.failed
              ? { background: "#fee2e2", borderColor: "#fca5a5", color: "#991b1b", maxWidth: "100%" }
              : { maxWidth: "100%" }
          }
        >
          {message.failed && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 700, marginBottom: 6 }}>
              <AlertTriangle size={14} /> Request failed
            </div>
          )}
          <MarkdownText text={message.content} />
        </div>

        {!isUser && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <button
              onClick={copyText}
              title="Copy answer"
              style={{
                display: "flex", alignItems: "center", gap: 5, fontSize: 11.5, fontWeight: 500,
                padding: "3px 8px", borderRadius: 6, border: "1px solid var(--border)",
                background: "none", color: "var(--muted-foreground)", cursor: "pointer",
              }}
            >
              {copied ? <Check size={11} /> : <Copy size={11} />} {copied ? "Copied" : "Copy"}
            </button>

            {message.meta && (
              <>
                {message.meta.agent_keys.length > 0 && (
                  <span style={{ fontSize: 11.5, color: "var(--muted-foreground)" }}>
                    Agents: {message.meta.agent_keys
                      .map(key => AGENT_LABELS[key as AgentKey] ?? key)
                      .join(", ")}
                  </span>
                )}
                {message.meta.tenant && (
                  <span style={{ fontSize: 11.5, color: "var(--muted-foreground)" }}>
                    {message.meta.tenant}
                    {message.meta.environment ? ` · ${message.meta.environment}` : ""}
                    {message.meta.machine_reference ? ` · ${message.meta.machine_reference}` : ""}
                  </span>
                )}
                {!message.meta.conversation_saved && (
                  <span
                    title="The orchestrator could not persist this turn to the conversation history API."
                    style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11.5, color: "#d97706" }}
                  >
                    <CloudOff size={11} /> Not saved to history
                  </span>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, sending])

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sending) return

    const userMessage: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    }
    setMessages(current => [...current, userMessage])
    setInput("")
    setSending(true)

    try {
      // The orchestrator identifies the user by the email it will store on the
      // conversation turn, which is the same subject the Spring JWT carries.
      const response = await chatApi.send({
        user_id: user?.email ?? "unknown",
        message: trimmed,
      })
      setMessages(current => [
        ...current,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: response.answer || "The agents returned no data for this request.",
          timestamp: new Date(),
          meta: response,
        },
      ])
    } catch (error) {
      // An unreachable or failing orchestrator is rendered as an explicit
      // failure, never as an empty answer.
      setMessages(current => [
        ...current,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          content: describeError(error),
          timestamp: new Date(),
          failed: true,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 56px)" }}>
      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "24px 24px 8px" }}>
        <div style={{ maxWidth: 820, margin: "0 auto", display: "flex", flexDirection: "column", gap: 18 }}>
          {messages.length === 0 && !sending && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 40 }}>
              <div style={{
                width: 48, height: 48, borderRadius: 12,
                background: "linear-gradient(135deg, #4f46e5, #6366f1)",
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: "0 0 24px rgba(99,102,241,0.35)",
              }}>
                <Sparkles size={22} color="white" />
              </div>
              <div style={{ textAlign: "center" }}>
                <h2 style={{ fontSize: 19, fontWeight: 800, letterSpacing: "-0.02em" }}>Ask about your environments</h2>
                <p style={{ fontSize: 13.5, color: "var(--muted-foreground)", marginTop: 4, maxWidth: 460, lineHeight: 1.6 }}>
                  Questions are routed to the Git, Jenkins, Installation, Logs and Infrastructure
                  agents on the machine assigned to your client.
                </p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 8, width: "100%", maxWidth: 640 }}>
                {SUGGESTIONS.map(suggestion => (
                  <button
                    key={suggestion.text}
                    onClick={() => send(suggestion.text)}
                    style={{
                      display: "flex", alignItems: "center", gap: 10, textAlign: "left",
                      padding: "10px 14px", borderRadius: 8, fontSize: 13,
                      background: "var(--card)", border: "1px solid var(--border)",
                      color: "var(--foreground)", cursor: "pointer", transition: "all 0.15s",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--primary)")}
                    onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
                  >
                    <span style={{ color: "var(--primary)", display: "flex" }}>{suggestion.icon}</span>
                    {suggestion.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(message => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {sending && (
            <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
              <div style={{
                width: 30, height: 30, borderRadius: 8, flexShrink: 0,
                background: "color-mix(in srgb, var(--primary) 14%, transparent)",
                color: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <Bot size={15} />
              </div>
              <div className="chat-bubble-ai">
                <TypingIndicator />
                <div style={{ fontSize: 12, color: "var(--muted-foreground)", marginTop: 4 }}>
                  Running agents. This can take a few minutes.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ borderTop: "1px solid var(--border)", background: "var(--card)", padding: "14px 24px" }}>
        <form
          onSubmit={event => {
            event.preventDefault()
            send(input)
          }}
          style={{ maxWidth: 820, margin: "0 auto", display: "flex", gap: 10, alignItems: "flex-end" }}
        >
          <textarea
            className="input-field"
            placeholder="Ask about a deployment, a build, a server..."
            value={input}
            onChange={event => setInput(event.target.value)}
            onKeyDown={event => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault()
                send(input)
              }
            }}
            rows={1}
            style={{ resize: "none", minHeight: 44, maxHeight: 160, paddingTop: 12, paddingBottom: 12 }}
          />
          <button type="submit" className="btn-primary" disabled={sending || !input.trim()} style={{ height: 44, padding: "0 18px" }}>
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  )
}
