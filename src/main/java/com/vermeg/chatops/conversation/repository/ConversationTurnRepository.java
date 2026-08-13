package com.vermeg.chatops.conversation.repository;

import com.vermeg.chatops.conversation.entity.ConversationTurnEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ConversationTurnRepository extends JpaRepository<ConversationTurnEntity, UUID> {

    List<ConversationTurnEntity> findByNormalizedUserIdOrderByTurnTimestampDesc(
            String normalizedUserId,
            Pageable pageable
    );

    long countByNormalizedUserId(String normalizedUserId);
}
