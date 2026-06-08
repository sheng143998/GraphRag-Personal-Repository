package com.example.agentknowledge.service;

import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.LearningWeakPoint;
import com.example.agentknowledge.dto.agent.AgentInvokeResponse;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.dto.chat.UpdateLearningWeakPointRequest;
import com.example.agentknowledge.repository.LearningWeakPointRepository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LearningWeakPointService {

    private final LearningWeakPointRepository learningWeakPointRepository;
    private final ChatService chatService;

    public LearningWeakPointService(
            LearningWeakPointRepository learningWeakPointRepository,
            ChatService chatService
    ) {
        this.learningWeakPointRepository = learningWeakPointRepository;
        this.chatService = chatService;
    }

    @Transactional
    public List<LearningWeakPointResponse> recordReviewCards(
            ChatSession session,
            ChatMessage evidenceMessage,
            List<AgentInvokeResponse.ReviewCard> reviewCards
    ) {
        if (reviewCards == null || reviewCards.isEmpty()) {
            return listWeakPoints(session.getId());
        }
        for (AgentInvokeResponse.ReviewCard card : reviewCards) {
            String topic = normalizeTopic(card.question());
            if (topic.isBlank()) {
                continue;
            }
            LearningWeakPoint weakPoint = learningWeakPointRepository
                    .findBySession_IdAndTopicIgnoreCase(session.getId(), topic)
                    .orElseGet(() -> createWeakPoint(session, topic));
            weakPoint.setKnowledgeBase(session.getKnowledgeBase());
            weakPoint.setEvidenceMessage(evidenceMessage);
            weakPoint.setExpectedAnswer(card.expectedAnswer());
            weakPoint.setSourceHint(card.sourceHint() != null ? card.sourceHint() : "");
            weakPoint.setDifficulty(card.difficulty() != null && !card.difficulty().isBlank() ? card.difficulty() : "medium");
            weakPoint.setReviewCount(weakPoint.getId() == null ? 1 : weakPoint.getReviewCount() + 1);
            weakPoint.setLastSeenAt(Instant.now());
            learningWeakPointRepository.save(weakPoint);
        }
        return listWeakPoints(session.getId());
    }

    @Transactional(readOnly = true)
    public List<LearningWeakPointResponse> listWeakPoints(UUID sessionId) {
        chatService.getSession(sessionId);
        return learningWeakPointRepository.findPrioritizedBySessionId(sessionId, PageRequest.of(0, 20))
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional
    public LearningWeakPointResponse updateWeakPoint(
            UUID sessionId,
            UUID weakPointId,
            UpdateLearningWeakPointRequest request
    ) {
        chatService.getSession(sessionId);
        LearningWeakPoint weakPoint = learningWeakPointRepository.findByIdAndSession_Id(weakPointId, sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Learning weak point not found: " + weakPointId));
        String status = normalizeMasteryStatus(request.masteryStatus());
        weakPoint.setMasteryStatus(status);
        weakPoint.setLastAssessedAt(Instant.now());
        if ("MASTERED".equals(status)) {
            weakPoint.setDifficulty("easy");
        }
        return toResponse(learningWeakPointRepository.save(weakPoint));
    }

    @Transactional(readOnly = true)
    public LearningWeakPoint getWeakPoint(UUID sessionId, UUID weakPointId) {
        chatService.getSession(sessionId);
        return learningWeakPointRepository.findByIdAndSession_Id(weakPointId, sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Learning weak point not found: " + weakPointId));
    }

    private LearningWeakPoint createWeakPoint(ChatSession session, String topic) {
        LearningWeakPoint weakPoint = new LearningWeakPoint();
        weakPoint.setSession(session);
        weakPoint.setTopic(topic);
        weakPoint.setReviewCount(0);
        return weakPoint;
    }

    private static String normalizeTopic(String value) {
        return value == null ? "" : value.trim().replaceAll("\\s+", " ");
    }

    private static String normalizeMasteryStatus(String value) {
        String status = value == null ? "" : value.trim().toUpperCase();
        if (!status.equals("MASTERED") && !status.equals("NEEDS_REVIEW")) {
            throw new IllegalArgumentException("Unsupported masteryStatus: " + value);
        }
        return status;
    }

    public LearningWeakPointResponse toResponse(LearningWeakPoint weakPoint) {
        return new LearningWeakPointResponse(
                weakPoint.getId(),
                weakPoint.getSession().getId(),
                weakPoint.getKnowledgeBase() != null ? weakPoint.getKnowledgeBase().getId() : null,
                weakPoint.getEvidenceMessage() != null ? weakPoint.getEvidenceMessage().getId() : null,
                weakPoint.getTopic(),
                weakPoint.getExpectedAnswer(),
                weakPoint.getSourceHint(),
                weakPoint.getDifficulty(),
                weakPoint.getMasteryStatus(),
                weakPoint.getReviewCount(),
                weakPoint.getLastSeenAt(),
                weakPoint.getLastAssessedAt(),
                weakPoint.getCreatedAt()
        );
    }

}
