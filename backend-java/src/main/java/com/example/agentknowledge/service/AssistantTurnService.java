package com.example.agentknowledge.service;

import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.dto.agent.AgentInvokeRequest;
import com.example.agentknowledge.dto.agent.AgentInvokeResponse;
import com.example.agentknowledge.dto.chat.AssistantTurnResponse;
import com.example.agentknowledge.dto.chat.ChatMessageResponse;
import com.example.agentknowledge.dto.chat.CreateAssistantTurnRequest;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.repository.ChatMessageRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AssistantTurnService {

    private final ChatService chatService;
    private final ChatMessageRepository chatMessageRepository;
    private final AgentService agentService;
    private final LearningWeakPointService learningWeakPointService;
    private final ObjectMapper objectMapper;

    public AssistantTurnService(
            ChatService chatService,
            ChatMessageRepository chatMessageRepository,
            AgentService agentService,
            LearningWeakPointService learningWeakPointService,
            ObjectMapper objectMapper
    ) {
        this.chatService = chatService;
        this.chatMessageRepository = chatMessageRepository;
        this.agentService = agentService;
        this.learningWeakPointService = learningWeakPointService;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public AssistantTurnResponse runTurn(UUID sessionId, CreateAssistantTurnRequest request) {
        ChatSession session = chatService.getSession(sessionId);
        if (session.getKnowledgeBase() == null) {
            throw new IllegalArgumentException("Chat session must be linked to a knowledge base before invoking assistant turn.");
        }

        ChatMessage userMessage = saveMessage(session, "user", request.userInput(), "[]");
        AgentInvokeResponse agentResponse = agentService.invoke(new AgentInvokeRequest(
                request.agentName(),
                request.userInput(),
                request.strategyName(),
                request.topK(),
                session.getKnowledgeBase().getId(),
                session.getId(),
                userMessage.getId(),
                request.metadataFilters(),
                request.variables()
        ));
        ChatMessage assistantMessage = saveMessage(
                session,
                "assistant",
                agentResponse.output(),
                serializeCitations(agentResponse)
        );
        java.util.List<LearningWeakPointResponse> weakPoints = learningWeakPointService.recordReviewCards(
                session,
                assistantMessage,
                agentResponse.reviewCards()
        );

        return new AssistantTurnResponse(
                toMessageResponse(userMessage),
                toMessageResponse(assistantMessage),
                agentResponse.agentName(),
                agentResponse.questionType(),
                agentResponse.selectedStrategyName(),
                agentResponse.followUpQuestions(),
                agentResponse.studyPlan(),
                agentResponse.reviewCards(),
                weakPoints,
                agentResponse.workflowSteps(),
                agentResponse.trace()
        );
    }

    private ChatMessage saveMessage(ChatSession session, String role, String content, String citations) {
        ChatMessage message = new ChatMessage();
        message.setSession(session);
        message.setRole(role);
        message.setContent(content);
        message.setCitations(citations);
        message.setTraceId(TraceContext.getTraceId());
        return chatMessageRepository.save(message);
    }

    private String serializeCitations(AgentInvokeResponse agentResponse) {
        try {
            return objectMapper.writeValueAsString(agentResponse.citations() == null ? java.util.List.of() : agentResponse.citations());
        } catch (JsonProcessingException exception) {
            return objectMapper.valueToTree(Map.of("serializationError", exception.getMessage())).toString();
        }
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
