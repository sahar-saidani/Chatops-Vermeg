import NotImplementedPage from "./NotImplementedPage"
import { AGENT_LABELS } from "../types"
import type { AgentKey } from "../types"

export default function AgentPage({ agentKey }: { agentKey: AgentKey }) {
  return (
    <NotImplementedPage
      title={AGENT_LABELS[agentKey]}
      reason="Agent event retrieval is not connected yet."
    />
  )
}
