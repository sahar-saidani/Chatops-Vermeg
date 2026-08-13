package com.vermeg.chatops.conversation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;

/**
 * The payload llm-orchestrator/data/conversation_history_client.py already
 * sends.
 *
 * <p>The snake_case field names are the orchestrator's, not this codebase's
 * convention. They are honoured via {@link JsonProperty} rather than renamed
 * because the client predates this endpoint and adapting the consumer is the
 * cheaper, less breakable side of the contract.
 */
public record RecordConversationTurnRequest(
        @JsonProperty("user_id")
        @NotBlank(message = "user_id is required")
        @Size(max = 320, message = "user_id must not exceed 320 characters")
        String userId,

        @JsonProperty("request_mode")
        @NotBlank(message = "request_mode is required")
        @Size(max = 64, message = "request_mode must not exceed 64 characters")
        String requestMode,

        @Size(max = 160, message = "tenant must not exceed 160 characters")
        String tenant,

        @Size(max = 64, message = "environment must not exceed 64 characters")
        String environment,

        @JsonProperty("agent_keys")
        @NotNull(message = "agent_keys is required")
        List<String> agentKeys,

        @JsonProperty("user_message")
        @NotBlank(message = "user_message is required")
        String userMessage,

        @JsonProperty("assistant_response")
        @NotBlank(message = "assistant_response is required")
        String assistantResponse,

        /** ISO-8601 instant produced by datetime.now(timezone.utc).isoformat(). */
        String timestamp
) {
}
