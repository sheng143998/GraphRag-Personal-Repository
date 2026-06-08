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
        when(repository.findTop20BySession_IdOrderByLastSeenAtDesc(sessionId)).thenAnswer(invocation -> stored);

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
}
