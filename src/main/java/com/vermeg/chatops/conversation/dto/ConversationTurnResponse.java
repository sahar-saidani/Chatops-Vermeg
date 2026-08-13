package com.vermeg.chatops.conversation.dto;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

/**
 * Read model for the history page. Uses this codebase's camelCase convention:
 * only the ingest payload has to match the orchestrator's naming.
 */
public record ConversationTurnResponse(
        UUID id,
        String userId,
        String requestMode,
        String tenant,
        String environment,
        List<String> agentKeys,
        String userMessage,
        String assistantResponse,
        Instant timestamp
) {
}
