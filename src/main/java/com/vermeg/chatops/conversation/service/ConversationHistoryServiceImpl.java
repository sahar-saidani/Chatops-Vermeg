package com.vermeg.chatops.conversation.service;

import com.vermeg.chatops.conversation.dto.ConversationTurnResponse;
import com.vermeg.chatops.conversation.dto.RecordConversationTurnRequest;
import com.vermeg.chatops.conversation.entity.ConversationTurnEntity;
import com.vermeg.chatops.conversation.repository.ConversationTurnRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.List;

@Service
@Transactional(readOnly = true)
public class ConversationHistoryServiceImpl implements ConversationHistoryService {

    private final ConversationTurnRepository conversationTurnRepository;

    public ConversationHistoryServiceImpl(ConversationTurnRepository conversationTurnRepository) {
        this.conversationTurnRepository = conversationTurnRepository;
    }

    @Override
    @Transactional
    public ConversationTurnResponse record(RecordConversationTurnRequest request) {
        ConversationTurnEntity entity = new ConversationTurnEntity(
                request.userId(),
                request.requestMode(),
                request.tenant(),
                request.environment(),
                request.agentKeys(),
                request.userMessage(),
                request.assistantResponse(),
                parseTimestamp(request.timestamp())
        );
        return toResponse(conversationTurnRepository.save(entity));
    }

    @Override
    public List<ConversationTurnResponse> findOwnHistory(String userEmail, int limit) {
        return conversationTurnRepository
                .findByNormalizedUserIdOrderByTurnTimestampDesc(
                        ConversationTurnEntity.normalize(userEmail),
                        PageRequest.of(0, limit)
                )
                .stream()
                .map(ConversationHistoryServiceImpl::toResponse)
                .toList();
    }

    /**
     * The orchestrator sends an offset-aware ISO-8601 string. A malformed or
     * absent value falls back to "now" rather than rejecting the write: losing
     * the turn entirely would be a worse outcome than an approximate timestamp,
     * and the orchestrator treats a failed save as non-fatal anyway.
     */
    private static Instant parseTimestamp(String timestamp) {
        if (timestamp == null || timestamp.isBlank()) {
            return Instant.now();
        }
        try {
            return OffsetDateTime.parse(timestamp).toInstant();
        } catch (DateTimeParseException ignored) {
            try {
                return Instant.parse(timestamp);
            } catch (DateTimeParseException alsoIgnored) {
                return Instant.now();
            }
        }
    }

    private static ConversationTurnResponse toResponse(ConversationTurnEntity entity) {
        return new ConversationTurnResponse(
                entity.getId(),
                entity.getUserId(),
                entity.getRequestMode(),
                entity.getTenant(),
                entity.getEnvironment(),
                entity.getAgentKeys(),
                entity.getUserMessage(),
                entity.getAssistantResponse(),
                entity.getTurnTimestamp()
        );
    }
}
