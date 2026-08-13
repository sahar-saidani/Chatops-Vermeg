package com.vermeg.chatops.conversation.service;

import com.vermeg.chatops.conversation.dto.ConversationTurnResponse;
import com.vermeg.chatops.conversation.dto.RecordConversationTurnRequest;

import java.util.List;

public interface ConversationHistoryService {

    ConversationTurnResponse record(RecordConversationTurnRequest request);

    /** Turns belonging to {@code userEmail} only, most recent first. */
    List<ConversationTurnResponse> findOwnHistory(String userEmail, int limit);
}
