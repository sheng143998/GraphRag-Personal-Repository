package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.LearningWeakPoint;
import com.example.agentknowledge.dto.agent.AgentInvokeResponse;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.dto.chat.UpdateLearningWeakPointRequest;
import com.example.agentknowledge.repository.LearningWeakPointRepository;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;

class LearningWeakPointServiceTest {

    private final LearningWeakPointRepository repository = mock(LearningWeakPointRepository.class);
    private final ChatService chatService = mock(ChatService.class);
    private final LearningWeakPointService service = new LearningWeakPointService(repository, chatService);

    @Test
    void recordReviewCardsCreatesAndUpdatesSessionWeakPoints() {
        UUID sessionId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        session.setKnowledgeBase(knowledgeBase);
        ChatMessage message = new ChatMessage();
        message.setId(UUID.randomUUID());

        List<LearningWeakPoint> stored = new ArrayList<>();
        when(repository.findBySession_IdAndTopicIgnoreCase(sessionId, "How would you prove rerank works?"))
                .thenReturn(Optional.empty());
        when(repository.save(org.mockito.ArgumentMatchers.any(LearningWeakPoint.class))).thenAnswer(invocation -> {
            LearningWeakPoint weakPoint = invocation.getArgument(0);
            weakPoint.setId(UUID.randomUUID());
            stored.add(weakPoint);
            return weakPoint;
        });
        when(chatService.getSession(sessionId)).thenReturn(session);
        when(repository.findPrioritizedBySessionId(org.mockito.ArgumentMatchers.eq(sessionId), ArgumentMatchers.any()))
                .thenAnswer(invocation -> stored);

        List<LearningWeakPointResponse> responses = service.recordReviewCards(
                session,
                message,
                List.of(new AgentInvokeResponse.ReviewCard(
                        "How would you prove rerank works?",
                        "Use an end-to-end trace assertion.",
                        "source",
                        "hard"
                ))
        );

        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).topic()).isEqualTo("How would you prove rerank works?");
        assertThat(responses.get(0).reviewCount()).isEqualTo(1);
        assertThat(responses.get(0).difficulty()).isEqualTo("hard");
        assertThat(responses.get(0).masteryStatus()).isEqualTo("NEEDS_REVIEW");
    }

    @Test
    void updateWeakPointStoresMasteryStatusAndAssessmentTime() {
        UUID sessionId = UUID.randomUUID();
        UUID weakPointId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        LearningWeakPoint weakPoint = new LearningWeakPoint();
        weakPoint.setId(weakPointId);
        weakPoint.setSession(session);
        weakPoint.setTopic("How would you prove rerank works?");
        weakPoint.setDifficulty("hard");
        weakPoint.setReviewCount(2);

        when(chatService.getSession(sessionId)).thenReturn(session);
        when(repository.findByIdAndSession_Id(weakPointId, sessionId)).thenReturn(Optional.of(weakPoint));
        when(repository.save(weakPoint)).thenReturn(weakPoint);

        LearningWeakPointResponse response = service.updateWeakPoint(
                sessionId,
                weakPointId,
                new UpdateLearningWeakPointRequest("MASTERED")
        );

        assertThat(response.masteryStatus()).isEqualTo("MASTERED");
        assertThat(response.difficulty()).isEqualTo("easy");
        assertThat(response.lastAssessedAt()).isNotNull();
    }

    @Test
    void assessPracticeAnswerMastersHighOverlapAnswer() {
        UUID sessionId = UUID.randomUUID();
        UUID weakPointId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        LearningWeakPoint weakPoint = weakPoint(session, "Rerank evidence", "NEEDS_REVIEW", "hard", 2);
        weakPoint.setId(weakPointId);
        weakPoint.setExpectedAnswer("Use rerank score and trace evidence to prove retrieval quality.");

        when(chatService.getSession(sessionId)).thenReturn(session);
        when(repository.findByIdAndSession_Id(weakPointId, sessionId)).thenReturn(Optional.of(weakPoint));
        when(repository.save(weakPoint)).thenReturn(weakPoint);

        var result = service.assessPracticeAnswer(
                sessionId,
                weakPointId,
                "Use rerank score and trace evidence to prove retrieval quality."
        );

        assertThat(result.assessment().passed()).isTrue();
        assertThat(result.assessment().masteryStatus()).isEqualTo("MASTERED");
        assertThat(result.updatedWeakPoint().masteryStatus()).isEqualTo("MASTERED");
        assertThat(result.updatedWeakPoint().difficulty()).isEqualTo("easy");
        assertThat(result.updatedWeakPoint().reviewCount()).isEqualTo(3);
        assertThat(result.updatedWeakPoint().lastAssessedAt()).isNotNull();
    }

    @Test
    void assessPracticeAnswerKeepsLowOverlapAnswerNeedsReview() {
        UUID sessionId = UUID.randomUUID();
        UUID weakPointId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        LearningWeakPoint weakPoint = weakPoint(session, "Graph traversal", "NEEDS_REVIEW", "medium", 1);
        weakPoint.setId(weakPointId);
        weakPoint.setExpectedAnswer("Graph traversal expands entity relationships for citations.");

        when(chatService.getSession(sessionId)).thenReturn(session);
        when(repository.findByIdAndSession_Id(weakPointId, sessionId)).thenReturn(Optional.of(weakPoint));
        when(repository.save(weakPoint)).thenReturn(weakPoint);

        var result = service.assessPracticeAnswer(sessionId, weakPointId, "CRUD screens manage forms.");

        assertThat(result.assessment().passed()).isFalse();
        assertThat(result.assessment().masteryStatus()).isEqualTo("NEEDS_REVIEW");
        assertThat(result.updatedWeakPoint().masteryStatus()).isEqualTo("NEEDS_REVIEW");
        assertThat(result.updatedWeakPoint().difficulty()).isEqualTo("hard");
        assertThat(result.updatedWeakPoint().reviewCount()).isEqualTo(2);
    }

    @Test
    void listWeakPointsUsesPrioritizedReviewOrder() {
        UUID sessionId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        LearningWeakPoint needsReview = weakPoint(session, "Needs graph traversal practice", "NEEDS_REVIEW", "hard", 3);
        LearningWeakPoint mastered = weakPoint(session, "Already mastered rerank", "MASTERED", "easy", 8);

        when(chatService.getSession(sessionId)).thenReturn(session);
        when(repository.findPrioritizedBySessionId(org.mockito.ArgumentMatchers.eq(sessionId), ArgumentMatchers.any()))
                .thenReturn(List.of(needsReview, mastered));

        List<LearningWeakPointResponse> responses = service.listWeakPoints(sessionId);

        assertThat(responses).extracting(LearningWeakPointResponse::masteryStatus)
                .containsExactly("NEEDS_REVIEW", "MASTERED");
        assertThat(responses.get(0).topic()).isEqualTo("Needs graph traversal practice");
    }

    @Test
    void summarizeWeakPointsReturnsProgressAndNextReviewItem() {
        UUID sessionId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        LearningWeakPoint needsReview = weakPoint(session, "Needs graph traversal practice", "NEEDS_REVIEW", "hard", 3);
        LearningWeakPoint mastered = weakPoint(session, "Already mastered rerank", "MASTERED", "easy", 8);

        when(chatService.getSession(sessionId)).thenReturn(session);
        when(repository.findBySession_Id(sessionId)).thenReturn(List.of(needsReview, mastered));
        when(repository.findPrioritizedBySessionId(org.mockito.ArgumentMatchers.eq(sessionId), ArgumentMatchers.any()))
                .thenReturn(List.of(needsReview));

        var summary = service.summarizeWeakPoints(sessionId);

        assertThat(summary.totalCount()).isEqualTo(2);
        assertThat(summary.needsReviewCount()).isEqualTo(1);
        assertThat(summary.masteredCount()).isEqualTo(1);
        assertThat(summary.hardCount()).isEqualTo(1);
        assertThat(summary.totalReviewCount()).isEqualTo(11);
        assertThat(summary.completionRate()).isEqualTo(0.5);
        assertThat(summary.nextWeakPoint().topic()).isEqualTo("Needs graph traversal practice");
    }

    private static LearningWeakPoint weakPoint(
            ChatSession session,
            String topic,
            String masteryStatus,
            String difficulty,
            int reviewCount
    ) {
        LearningWeakPoint weakPoint = new LearningWeakPoint();
        weakPoint.setId(UUID.randomUUID());
        weakPoint.setSession(session);
        weakPoint.setTopic(topic);
        weakPoint.setMasteryStatus(masteryStatus);
        weakPoint.setDifficulty(difficulty);
        weakPoint.setReviewCount(reviewCount);
        weakPoint.setLastSeenAt(java.time.Instant.now());
        return weakPoint;
    }
}
