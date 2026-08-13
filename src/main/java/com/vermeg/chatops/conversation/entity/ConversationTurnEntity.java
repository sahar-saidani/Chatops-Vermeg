package com.vermeg.chatops.conversation.entity;

import com.vermeg.chatops.common.persistence.AuditableEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.List;
import java.util.Locale;

/**
 * One exchange between a user and the LLM orchestrator.
 *
 * <p>The orchestrator identifies the user by the same string the Spring JWT
 * carries as its subject (the email address), so {@code normalizedUserId}
 * mirrors the lowercase form used everywhere else in the codebase and is what
 * ownership checks compare against.
 */
@Entity
@Table(name = "conversation_turns")
public class ConversationTurnEntity extends AuditableEntity {

    /** Stored on a single column rather than a child table: the list is short, read whole, and never queried by element. */
    private static final String AGENT_KEY_SEPARATOR = ",";

    @Column(name = "user_id", nullable = false, length = 320)
    private String userId;

    @Column(name = "normalized_user_id", nullable = false, length = 320)
    private String normalizedUserId;

    @Column(name = "request_mode", nullable = false, length = 64)
    private String requestMode;

    @Column(length = 160)
    private String tenant;

    @Column(length = 64)
    private String environment;

    @Column(name = "agent_keys", nullable = false, length = 512)
    private String agentKeys;

    @Column(name = "user_message", nullable = false, columnDefinition = "text")
    private String userMessage;

    @Column(name = "assistant_response", nullable = false, columnDefinition = "text")
    private String assistantResponse;

    @Column(name = "turn_timestamp", nullable = false)
    private Instant turnTimestamp;

    protected ConversationTurnEntity() {
    }

    public ConversationTurnEntity(
            String userId,
            String requestMode,
            String tenant,
            String environment,
            List<String> agentKeys,
            String userMessage,
            String assistantResponse,
            Instant turnTimestamp
    ) {
        this.userId = userId.strip();
        this.normalizedUserId = normalize(userId);
        this.requestMode = requestMode;
        this.tenant = tenant;
        this.environment = environment;
        this.agentKeys = agentKeys == null ? "" : String.join(AGENT_KEY_SEPARATOR, agentKeys);
        this.userMessage = userMessage;
        this.assistantResponse = assistantResponse;
        this.turnTimestamp = turnTimestamp;
    }

    public static String normalize(String userId) {
        return userId.strip().toLowerCase(Locale.ROOT);
    }

    public String getUserId() {
        return userId;
    }

    public String getNormalizedUserId() {
        return normalizedUserId;
    }

    public String getRequestMode() {
        return requestMode;
    }

    public String getTenant() {
        return tenant;
    }

    public String getEnvironment() {
        return environment;
    }

    public List<String> getAgentKeys() {
        return agentKeys.isBlank() ? List.of() : List.of(agentKeys.split(AGENT_KEY_SEPARATOR));
    }

    public String getUserMessage() {
        return userMessage;
    }

    public String getAssistantResponse() {
        return assistantResponse;
    }

    public Instant getTurnTimestamp() {
        return turnTimestamp;
    }
}
