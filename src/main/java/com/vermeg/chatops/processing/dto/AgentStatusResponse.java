package com.vermeg.chatops.processing.dto;

import java.time.Instant;

/**
 * What {@code canonical_events} can honestly say about one agent.
 *
 * <p>Only three statuses are reported, because only three are provable from
 * stored reports:
 * <ul>
 *   <li>{@code NO_DATA} - the agent has never delivered a report.</li>
 *   <li>{@code ONLINE} - its most recent report is inside the freshness window.</li>
 *   <li>{@code STALE} - it has reported before, but not recently.</li>
 * </ul>
 *
 * <p>RUNNING, FAILED and TIMEOUT are properties of a live orchestrator run,
 * not of the event store: a crashed agent writes nothing, which is
 * indistinguishable here from one that was never asked to run. Those states
 * reach the UI from a chat request's result instead, and must never be
 * inferred from an absence of rows.
 */
public record AgentStatusResponse(
        String agentKey,
        String status,
        Instant lastEventAt,
        long eventCount,
        String tenant,
        String environment,
        String machineReference
) {
}
