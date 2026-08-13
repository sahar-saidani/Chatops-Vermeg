-- Conversation history for the LLM orchestrator.
--
-- llm-orchestrator/data/conversation_history_client.py has been POSTing turns
-- to /api/v1/conversations since it was written, degrading to a logged warning
-- because no such endpoint existed. This table backs it.
--
-- One row per turn (user message + assistant answer) rather than a
-- conversation/message pair: that is exactly the unit the orchestrator sends,
-- and it has no notion of a conversation id to group turns under. Grouping can
-- be layered on later without rewriting what is stored here.
CREATE TABLE conversation_turns (
    id                 UUID PRIMARY KEY,
    created_at         TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at         TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by         VARCHAR(255),
    updated_by         VARCHAR(255),
    user_id            VARCHAR(320) NOT NULL,
    normalized_user_id VARCHAR(320) NOT NULL,
    request_mode       VARCHAR(64) NOT NULL,
    tenant             VARCHAR(160),
    environment        VARCHAR(64),
    agent_keys         VARCHAR(512) NOT NULL,
    user_message       TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    turn_timestamp     TIMESTAMP WITH TIME ZONE NOT NULL
);

-- The history endpoint always filters by owner and orders by recency.
CREATE INDEX ix_conversation_turns_user
    ON conversation_turns (normalized_user_id, turn_timestamp DESC);
