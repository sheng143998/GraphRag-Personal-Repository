package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.dto.agent.AgentInvokeRequest;
import com.example.agentknowledge.dto.agent.AgentInvokeResponse;
import com.example.agentknowledge.dto.chat.CreateAssistantTurnRequest;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.repository.ChatMessageRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class AssistantTurnServiceTest {

    private final ChatService chatService = mock(ChatService.class);
    private final ChatMessageRepository chatMessageRepository = mock(ChatMessageRepository.class);
    private final AgentService agentService = mock(AgentService.class);
    private final LearningWeakPointService learningWeakPointService = mock(LearningWeakPointService.class);
    private final RagRunRecorder ragRunRecorder = mock(RagRunRecorder.class);
    private final AssistantTurnService assistantTurnService = new AssistantTurnService(
            chatService,
            chatMessageRepository,
            agentService,
            learningWeakPointService,
            ragRunRecorder,
            new ObjectMapper()
    );

    @AfterEach
    void clearTrace() {
        TraceContext.clear();
    }

    @Test
    void runTurnStoresUserAndAssistantMessagesAndInvokesAgentWithMessageContext() {
        TraceContext.setTraceId("trace-turn");
        UUID sessionId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        ChatSession session = new ChatSession();
        session.setId(sessionId);
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        session.setKnowledgeBase(knowledgeBase);

        when(chatService.getSession(sessionId)).thenReturn(session);
        when(chatMessageRepository.save(any(ChatMessage.class))).thenAnswer(invocation -> {
            ChatMessage message = invocation.getArgument(0);
            if (message.getId() == null) {
                message.setId(UUID.randomUUID());
            }
            return message;
        });
        AiTraceMetadata agentTrace = new AiTraceMetadata(
                "trace-turn",
                "agent-run",
                "agent_invoke",
                "advanced-rag",
                "agent",
                "v1",
                "stub",
                "completed",
                8.0,
                Map.of("rag_rewritten_query", "graph rag interview answer"),
                List.of()
        );
        AiTraceMetadata ragTrace = new AiTraceMetadata(
                "trace-turn",
                "rag-run",
                "rag_query",
                "advanced-rag",
                "rag_answer",
                "v1",
                "stub",
                "completed",
                6.0,
                Map.of("rewritten_query", "graph rag interview answer"),
                List.of(Map.of("name", "query_rewrite", "status", "completed"))
        );
        when(agentService.invoke(any(AgentInvokeRequest.class))).thenReturn(new AgentInvokeResponse(
                "study-agent",
                "assistant answer",
                List.of(new AiSourceMetadata(null, null, "source", null, 0.9, null, null, null, Map.of("content_preview", "source"))),
                "interview",
                "advanced-rag",
                List.of("Can you give a 60-second interview answer?"),
                new AgentInvokeResponse.StudyPlan(
                        "Prepare an interview-ready explanation.",
                        List.of("interview", "advanced-rag"),
                        List.of("Review core terms.", "Practice a project story.", "Answer one follow-up.")
                ),
                List.of(new AgentInvokeResponse.ReviewCard(
                        "Give a 60-second answer.",
                        "State the concept, trade-off, and project proof.",
                        "source",
                        "medium"
                )),
                List.of(new AgentInvokeResponse.WorkflowStep("select_rag_strategy", "Selected strategy.", Map.of())),
                agentTrace,
                ragTrace
        ));
        when(learningWeakPointService.recordReviewCards(
                any(ChatSession.class),
                any(ChatMessage.class),
                org.mockito.ArgumentMatchers.anyList()
        )).thenReturn(List.of(new LearningWeakPointResponse(
                UUID.randomUUID(),
                sessionId,
                knowledgeBaseId,
                UUID.randomUUID(),
                "Give a 60-second answer.",
                "State the concept, trade-off, and project proof.",
                "source",
                "medium",
                "NEEDS_REVIEW",
                1,
                Instant.parse("2026-06-08T00:00:00Z"),
                null,
                0,
                null,
                Instant.parse("2026-06-08T00:00:00Z"),
                Instant.parse("2026-06-08T00:00:00Z")
        )));

        var response = assistantTurnService.runTurn(sessionId, new CreateAssistantTurnRequest(
                "Give me an interview answer for GraphRAG.",
                null,
                null,
                3,
                Map.of("topic", "graph-rag"),
                Map.of("vectorWeight", 0.6, "keywordWeight", 0.4),
                Map.of("mode", "interview")
        ));

        ArgumentCaptor<ChatMessage> messageCaptor = ArgumentCaptor.forClass(ChatMessage.class);
        verify(chatMessageRepository, org.mockito.Mockito.times(2)).save(messageCaptor.capture());
        List<ChatMessage> savedMessages = messageCaptor.getAllValues();
        assertThat(savedMessages.get(0).getRole()).isEqualTo("user");
        assertThat(savedMessages.get(0).getContent()).contains("GraphRAG");
        assertThat(savedMessages.get(1).getRole()).isEqualTo("assistant");
        assertThat(savedMessages.get(1).getContent()).isEqualTo("assistant answer");
        assertThat(savedMessages.get(1).getCitations()).contains("source");

        ArgumentCaptor<AgentInvokeRequest> agentRequest = ArgumentCaptor.forClass(AgentInvokeRequest.class);
        verify(agentService).invoke(agentRequest.capture());
        assertThat(agentRequest.getValue().knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(agentRequest.getValue().sessionId()).isEqualTo(sessionId);
        assertThat(agentRequest.getValue().messageId()).isEqualTo(savedMessages.get(0).getId());
        assertThat(agentRequest.getValue().metadataFilters()).containsEntry("topic", "graph-rag");
        assertThat(agentRequest.getValue().retrievalOptions())
                .containsEntry("vectorWeight", 0.6)
                .containsEntry("keywordWeight", 0.4);
        assertThat(agentRequest.getValue().variables()).containsEntry("mode", "interview");

        verify(ragRunRecorder).recordAgentRagRun(
                any(ChatSession.class),
                any(ChatMessage.class),
                any(KnowledgeBase.class),
                org.mockito.ArgumentMatchers.eq("Give me an interview answer for GraphRAG."),
                org.mockito.ArgumentMatchers.eq("assistant answer"),
                org.mockito.ArgumentMatchers.eq("advanced-rag"),
                org.mockito.ArgumentMatchers.anyList(),
                org.mockito.ArgumentMatchers.eq(agentTrace),
                org.mockito.ArgumentMatchers.eq(ragTrace)
        );

        assertThat(response.userMessage().role()).isEqualTo("user");
        assertThat(response.assistantMessage().role()).isEqualTo("assistant");
        assertThat(response.questionType()).isEqualTo("interview");
        assertThat(response.selectedStrategyName()).isEqualTo("advanced-rag");
        assertThat(response.followUpQuestions()).contains("Can you give a 60-second interview answer?");
        assertThat(response.studyPlan()).isNotNull();
        assertThat(response.studyPlan().steps()).contains("Practice a project story.");
        assertThat(response.reviewCards()).hasSize(1);
        assertThat(response.reviewCards().get(0).question()).contains("60-second");
        assertThat(response.weakPoints()).hasSize(1);
        assertThat(response.weakPoints().get(0).topic()).contains("60-second");
        assertThat(response.workflowSteps()).hasSize(1);
        assertThat(response.ragTrace()).isEqualTo(ragTrace);
    }
}
