package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.LearningWeakPoint;
import com.example.agentknowledge.dto.chat.AssistantTurnResponse;
import com.example.agentknowledge.dto.chat.ChatMessageResponse;
import com.example.agentknowledge.dto.chat.CreateAssistantTurnRequest;
import com.example.agentknowledge.dto.chat.CreateWeakPointPracticeTurnRequest;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.dto.chat.LearningWeakPointSummaryResponse;
import com.example.agentknowledge.dto.chat.WeakPointPracticeAssessmentResponse;
import com.example.agentknowledge.dto.chat.WeakPointPracticeTurnResponse;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class WeakPointPracticeServiceTest {

    private final LearningWeakPointService learningWeakPointService = mock(LearningWeakPointService.class);
    private final AssistantTurnService assistantTurnService = mock(AssistantTurnService.class);
    private final WeakPointPracticeService service = new WeakPointPracticeService(
            learningWeakPointService,
            assistantTurnService
    );

    @Test
    void runPracticeTurnBuildsAssistantTurnFromWeakPoint() {
        UUID sessionId = UUID.randomUUID();
        UUID weakPointId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        LearningWeakPoint weakPoint = new LearningWeakPoint();
        weakPoint.setId(weakPointId);
        weakPoint.setSession(session);
        weakPoint.setTopic("Graph traversal recall");
        weakPoint.setExpectedAnswer("Explain one-hop expansion evidence.");
        weakPoint.setSourceHint("graph notes");
        weakPoint.setDifficulty("hard");
        weakPoint.setMasteryStatus("NEEDS_REVIEW");
        weakPoint.setReviewCount(3);
        weakPoint.setLastSeenAt(Instant.parse("2026-06-08T00:00:00Z"));
        LearningWeakPointResponse weakPointResponse = new LearningWeakPointResponse(
                weakPointId,
                sessionId,
                null,
                null,
                "Graph traversal recall",
                "Explain one-hop expansion evidence.",
                "graph notes",
                "hard",
                "NEEDS_REVIEW",
                3,
                Instant.parse("2026-06-08T00:00:00Z"),
                null,
                0,
                null,
                Instant.parse("2026-06-08T00:00:00Z"),
                null
        );
        LearningWeakPointResponse updatedWeakPoint = new LearningWeakPointResponse(
                weakPointId,
                sessionId,
                null,
                null,
                "Graph traversal recall",
                "Explain one-hop expansion evidence.",
                "graph notes",
                "easy",
                "MASTERED",
                4,
                Instant.parse("2026-06-08T00:01:00Z"),
                Instant.parse("2026-06-08T00:01:00Z"),
                1,
                0.8,
                Instant.parse("2026-06-15T00:01:00Z"),
                null
        );
        WeakPointPracticeAssessmentResponse assessment = new WeakPointPracticeAssessmentResponse(
                0.8,
                true,
                "MASTERED",
                "easy",
                "Practice answer matched the expected weak-point answer at 80% overlap."
        );
        LearningWeakPointSummaryResponse summary = new LearningWeakPointSummaryResponse(
                1,
                0,
                1,
                0,
                4,
                0,
                1.0,
                updatedWeakPoint
        );
        when(learningWeakPointService.getWeakPoint(sessionId, weakPointId)).thenReturn(weakPoint);
        when(learningWeakPointService.toResponse(weakPoint)).thenReturn(weakPointResponse);
        when(learningWeakPointService.assessPracticeAnswer(sessionId, weakPointId, "My rough answer"))
                .thenReturn(new LearningWeakPointService.PracticeAssessmentResult(updatedWeakPoint, assessment));
        when(learningWeakPointService.summarizeWeakPoints(sessionId)).thenReturn(summary);
        AssistantTurnResponse assistantTurn = new AssistantTurnResponse(
                new ChatMessageResponse(UUID.randomUUID(), sessionId, "user", "practice", "[]", "trace", null),
                new ChatMessageResponse(UUID.randomUUID(), sessionId, "assistant", "answer", "[]", "trace", null),
                "study-agent",
                "interview",
                "advanced-rag",
                List.of(),
                null,
                List.of(),
                List.of(),
                List.of(),
                null
        );
        when(assistantTurnService.runTurn(org.mockito.ArgumentMatchers.eq(sessionId), org.mockito.ArgumentMatchers.any()))
                .thenReturn(assistantTurn);

        WeakPointPracticeTurnResponse response = service.runPracticeTurn(
                sessionId,
                weakPointId,
                new CreateWeakPointPracticeTurnRequest("advanced-rag", 4, "My rough answer", true)
        );

        ArgumentCaptor<CreateAssistantTurnRequest> request = ArgumentCaptor.forClass(CreateAssistantTurnRequest.class);
        verify(assistantTurnService).runTurn(org.mockito.ArgumentMatchers.eq(sessionId), request.capture());
        assertThat(request.getValue().userInput()).contains("Graph traversal recall");
        assertThat(request.getValue().userInput()).contains("Expected answer: Explain one-hop expansion evidence.");
        assertThat(request.getValue().userInput()).contains("My current answer: My rough answer");
        assertThat(request.getValue().variables()).containsEntry("mode", "weak-point-practice");
        assertThat(request.getValue().variables()).containsEntry("weakPointId", weakPointId.toString());
        assertThat(response.weakPoint().id()).isEqualTo(weakPointId);
        assertThat(response.updatedWeakPoint().masteryStatus()).isEqualTo("MASTERED");
        assertThat(response.assessment().passed()).isTrue();
        assertThat(response.summary().completionRate()).isEqualTo(1.0);
        assertThat(response.turn()).isSameAs(assistantTurn);
    }
}
