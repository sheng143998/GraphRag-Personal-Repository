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
        when(learningWeakPointService.getWeakPoint(sessionId, weakPointId)).thenReturn(weakPoint);
        when(learningWeakPointService.toResponse(weakPoint)).thenCallRealMethod();
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
                new CreateWeakPointPracticeTurnRequest("advanced-rag", 4, "My rough answer")
        );

        ArgumentCaptor<CreateAssistantTurnRequest> request = ArgumentCaptor.forClass(CreateAssistantTurnRequest.class);
        verify(assistantTurnService).runTurn(org.mockito.ArgumentMatchers.eq(sessionId), request.capture());
        assertThat(request.getValue().userInput()).contains("Graph traversal recall");
        assertThat(request.getValue().userInput()).contains("Expected answer: Explain one-hop expansion evidence.");
        assertThat(request.getValue().userInput()).contains("My current answer: My rough answer");
        assertThat(request.getValue().variables()).containsEntry("mode", "weak-point-practice");
        assertThat(request.getValue().variables()).containsEntry("weakPointId", weakPointId.toString());
        assertThat(response.weakPoint().id()).isEqualTo(weakPointId);
        assertThat(response.turn()).isSameAs(assistantTurn);
    }
}
