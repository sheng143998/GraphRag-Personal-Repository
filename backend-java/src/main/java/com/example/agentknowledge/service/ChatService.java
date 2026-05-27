package com.example.agentknowledge.service;

import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.dto.chat.ChatMessageResponse;
import com.example.agentknowledge.dto.chat.ChatSessionResponse;
import com.example.agentknowledge.dto.chat.CreateChatMessageRequest;
import com.example.agentknowledge.dto.chat.CreateChatSessionRequest;
import com.example.agentknowledge.repository.ChatMessageRepository;
import com.example.agentknowledge.repository.ChatSessionRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class ChatService {

    private final ChatSessionRepository chatSessionRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final KnowledgeBaseService knowledgeBaseService;

    public ChatService(
            ChatSessionRepository chatSessionRepository,
            ChatMessageRepository chatMessageRepository,
            KnowledgeBaseService knowledgeBaseService
    ) {
        this.chatSessionRepository = chatSessionRepository;
        this.chatMessageRepository = chatMessageRepository;
        this.knowledgeBaseService = knowledgeBaseService;
    }

    public ChatSessionResponse createSession(CreateChatSessionRequest request) {
        ChatSession session = new ChatSession();
        session.setTitle(request.title());
        if (request.knowledgeBaseId() != null) {
            KnowledgeBase knowledgeBase = knowledgeBaseService.getReference(request.knowledgeBaseId());
            session.setKnowledgeBase(knowledgeBase);
        }
        return toSessionResponse(chatSessionRepository.save(session));
    }

    public List<ChatSessionResponse> listSessions() {
        return chatSessionRepository.findAllByOrderByUpdatedAtDesc().stream().map(this::toSessionResponse).toList();
    }

    public ChatMessageResponse addMessage(UUID sessionId, CreateChatMessageRequest request) {
        ChatSession session = getSession(sessionId);
        ChatMessage message = new ChatMessage();
        message.setSession(session);
        message.setRole(request.role());
        message.setContent(request.content());
        message.setCitations(request.citations() == null || request.citations().isBlank() ? "[]" : request.citations());
        message.setTraceId(TraceContext.getTraceId());
        return toMessageResponse(chatMessageRepository.save(message));
    }

    public List<ChatMessageResponse> listMessages(UUID sessionId) {
        getSession(sessionId);
        return chatMessageRepository.findBySessionIdOrderByCreatedAtAsc(sessionId).stream()
                .map(this::toMessageResponse)
                .toList();
    }

    public ChatSession getSession(UUID sessionId) {
        return chatSessionRepository.findById(sessionId)
                .orElseThrow(() -> new ResourceNotFoundException("Chat session not found: " + sessionId));
    }

    public ChatMessage getMessage(UUID messageId) {
        return chatMessageRepository.findById(messageId)
                .orElseThrow(() -> new ResourceNotFoundException("Chat message not found: " + messageId));
    }

    private ChatSessionResponse toSessionResponse(ChatSession session) {
        return new ChatSessionResponse(
                session.getId(),
                session.getKnowledgeBase() == null ? null : session.getKnowledgeBase().getId(),
                session.getTitle(),
                session.getSessionStatus(),
                session.getCreatedAt(),
                session.getUpdatedAt()
        );
    }

    private ChatMessageResponse toMessageResponse(ChatMessage message) {
        return new ChatMessageResponse(
                message.getId(),
                message.getSession().getId(),
                message.getRole(),
                message.getContent(),
                message.getCitations(),
                message.getTraceId(),
                message.getCreatedAt()
        );
    }
}
