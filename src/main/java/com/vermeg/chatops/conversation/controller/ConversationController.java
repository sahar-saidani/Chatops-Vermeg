package com.vermeg.chatops.conversation.controller;

import com.vermeg.chatops.conversation.dto.ConversationTurnResponse;
import com.vermeg.chatops.conversation.dto.RecordConversationTurnRequest;
import com.vermeg.chatops.conversation.service.ConversationHistoryService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/conversations")
public class ConversationController {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 200;

    private final ConversationHistoryService conversationHistoryService;

    public ConversationController(ConversationHistoryService conversationHistoryService) {
        this.conversationHistoryService = conversationHistoryService;
    }

    /**
     * Ingest endpoint for the LLM orchestrator. Restricted to the internal
     * service authority so an ordinary user token cannot forge history rows
     * attributed to somebody else -- the owner comes from the request body,
     * which is only trustworthy from a trusted caller.
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAuthority('INTERNAL_SERVICE')")
    public ConversationTurnResponse record(@Valid @RequestBody RecordConversationTurnRequest request) {
        return conversationHistoryService.record(request);
    }

    /**
     * The caller's own history. There is deliberately no way to read another
     * user's conversations: the owner is taken from the authenticated
     * principal, never from a parameter.
     */
    @GetMapping
    public List<ConversationTurnResponse> findOwnHistory(
            Authentication authentication,
            @RequestParam(required = false) Integer limit
    ) {
        int effectiveLimit = limit == null ? DEFAULT_LIMIT : Math.min(Math.max(limit, 1), MAX_LIMIT);
        return conversationHistoryService.findOwnHistory(authentication.getName(), effectiveLimit);
    }
}
