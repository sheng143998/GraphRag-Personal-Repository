package com.example.agentknowledge.service;

import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.RagFeedback;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.feedback.CreateFeedbackRequest;
import com.example.agentknowledge.dto.feedback.FeedbackResponse;
import com.example.agentknowledge.repository.RagFeedbackRepository;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class FeedbackService {

    private final RagFeedbackRepository ragFeedbackRepository;
    private final RagService ragService;
    private final ChatService chatService;

    public FeedbackService(
            RagFeedbackRepository ragFeedbackRepository,
            RagService ragService,
            ChatService chatService
    ) {
        this.ragFeedbackRepository = ragFeedbackRepository;
        this.ragService = ragService;
        this.chatService = chatService;
    }

    public FeedbackResponse create(CreateFeedbackRequest request) {
        RagFeedback feedback = new RagFeedback();
        if (request.runId() != null) {
            RagRun run = ragService.getRunEntity(request.runId());
            feedback.setRun(run);
        }
        if (request.sessionId() != null) {
            ChatSession session = chatService.getSession(request.sessionId());
            feedback.setSession(session);
        }
        if (request.messageId() != null) {
            ChatMessage message = chatService.getMessage(request.messageId());
            feedback.setMessage(message);
        }
        feedback.setRating(request.rating());
        feedback.setFeedbackType(request.feedbackType());
        feedback.setComment(request.comment());
        return toResponse(ragFeedbackRepository.save(feedback));
    }

    private FeedbackResponse toResponse(RagFeedback feedback) {
        return new FeedbackResponse(
                feedback.getId(),
                feedback.getRun() == null ? null : feedback.getRun().getId(),
                feedback.getSession() == null ? null : feedback.getSession().getId(),
                feedback.getMessage() == null ? null : feedback.getMessage().getId(),
                feedback.getRating(),
                feedback.getFeedbackType(),
                feedback.getComment(),
                feedback.getCreatedAt()
        );
    }
}
