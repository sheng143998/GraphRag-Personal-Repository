package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagQueryRequest;
import com.example.agentknowledge.client.dto.AiRagQueryResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.RagQueryRequest;
import com.example.agentknowledge.dto.rag.RagQueryResponse;
import com.example.agentknowledge.dto.rag.RagRunSummaryResponse;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.PageRequest;
import org.mockito.ArgumentCaptor;

class RagServiceTest {

    private final RagRunRepository ragRunRepository = mock(RagRunRepository.class);
    private final RagRetrievalResultRepository ragRetrievalResultRepository = mock(RagRetrievalResultRepository.class);
    private final KnowledgeBaseService knowledgeBaseService = mock(KnowledgeBaseService.class);
    private final ChatService chatService = mock(ChatService.class);
    private final AiServiceGateway aiServiceGateway = mock(AiServiceGateway.class);
    private final DocumentChunkRepository documentChunkRepository = mock(DocumentChunkRepository.class);
    private final KnowledgeDocumentRepository knowledgeDocumentRepository = mock(KnowledgeDocumentRepository.class);

    private final RagService ragService = new RagService(
            ragRunRepository,
            ragRetrievalResultRepository,
            knowledgeBaseService,
            chatService,
            aiServiceGateway,
            documentChunkRepository,
            knowledgeDocumentRepository
    );

    @Test
    void queryPassesMetadataFiltersAndStoresRewrittenQuery() {
        UUID knowledgeBaseId = UUID.randomUUID();
        UUID missingDocumentId = UUID.randomUUID();
        UUID missingChunkId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        knowledgeBase.setName("Advanced RAG KB");
        RagRun savedRun = new RagRun();
        savedRun.setId(UUID.randomUUID());

        when(knowledgeBaseService.getReference(knowledgeBaseId)).thenReturn(knowledgeBase);
        when(ragRunRepository.save(any(RagRun.class))).thenAnswer(invocation -> {
            RagRun run = invocation.getArgument(0);
            if (run.getId() == null) {
                run.setId(savedRun.getId());
            }
            return run;
        });
        when(documentChunkRepository.findById(missingChunkId)).thenReturn(Optional.empty());
        when(knowledgeDocumentRepository.findById(missingDocumentId)).thenReturn(Optional.empty());
        when(aiServiceGateway.queryRag(any(AiRagQueryRequest.class), any())).thenReturn(
                new AiRagQueryResponse(
                        "How does advanced RAG use rerank?",
                        "Advanced RAG uses rewrite and rerank.",
                        List.of(new AiSourceMetadata(
                                missingDocumentId,
                                missingChunkId,
                                "Advanced RAG Notes",
                                null,
                                0.8,
                                0.9,
                                null,
                                null,
                                Map.of("content_preview", "Advanced RAG uses rewrite and rerank.")
                        )),
                        new AiTraceMetadata(
                                "trace-1",
                                "ai-run-1",
                                "rag_query",
                                "advanced-rag",
                                "rag_answer",
                                "v1",
                                "stub-llm",
                                "completed",
                                12.4,
                                Map.of("rewritten_query", "advanced rag retrieval augmented generation rerank")
                        )
                )
        );

        RagQueryResponse response = ragService.query(new RagQueryRequest(
                knowledgeBaseId,
                null,
                null,
                "How does advanced RAG use rerank?",
                "advanced-rag",
                "hybrid",
                Map.of("topic", "advanced-rag"),
                3
        ));

        assertThat(response.status()).isEqualTo("COMPLETED");
        assertThat(response.strategyName()).isEqualTo("advanced-rag");
        assertThat(response.citations()).hasSize(1);

        ArgumentCaptor<AiRagQueryRequest> aiRequest = ArgumentCaptor.forClass(AiRagQueryRequest.class);
        verify(aiServiceGateway).queryRag(aiRequest.capture(), any());
        assertThat(aiRequest.getValue().context().metadataFilters()).containsEntry("topic", "advanced-rag");

        ArgumentCaptor<RagRun> runCaptor = ArgumentCaptor.forClass(RagRun.class);
        verify(ragRunRepository, org.mockito.Mockito.atLeast(2)).save(runCaptor.capture());
        assertThat(runCaptor.getAllValues().getLast().getRewrittenQuery())
                .isEqualTo("advanced rag retrieval augmented generation rerank");

        ArgumentCaptor<List<RagRetrievalResult>> retrievalResults = ArgumentCaptor.forClass(List.class);
        verify(ragRetrievalResultRepository).saveAll(retrievalResults.capture());
        RagRetrievalResult result = retrievalResults.getValue().getFirst();
        assertThat(result.getDocument()).isNull();
        assertThat(result.getChunk()).isNull();
        assertThat(result.getRank()).isEqualTo(1);
        assertThat(result.getMetadata()).containsEntry("content_preview", "Advanced RAG uses rewrite and rerank.");
    }

    @Test
    void queryMarksRunFailedAndStoresErrorMessageWhenAiServiceFails() {
        RuntimeException failure = new RuntimeException("AI service unavailable");

        when(ragRunRepository.save(any(RagRun.class))).thenAnswer(invocation -> {
            RagRun run = invocation.getArgument(0);
            if (run.getId() == null) {
                run.setId(UUID.randomUUID());
            }
            return run;
        });
        when(aiServiceGateway.queryRag(any(AiRagQueryRequest.class), any())).thenThrow(failure);

        assertThatThrownBy(() -> ragService.query(new RagQueryRequest(
                null,
                null,
                null,
                "Why did the model fail?",
                null,
                null,
                null,
                null
        ))).isSameAs(failure);

        ArgumentCaptor<RagRun> runCaptor = ArgumentCaptor.forClass(RagRun.class);
        verify(ragRunRepository, org.mockito.Mockito.atLeast(2)).save(runCaptor.capture());
        RagRun failedRun = runCaptor.getAllValues().getLast();
        assertThat(failedRun.getStatus()).isEqualTo("FAILED");
        assertThat(failedRun.getErrorMessage()).isEqualTo("AI service unavailable");
    }

    @Test
    void queryDoesNotSaveRetrievalResultsWhenCitationsAreEmpty() {
        when(ragRunRepository.save(any(RagRun.class))).thenAnswer(invocation -> {
            RagRun run = invocation.getArgument(0);
            if (run.getId() == null) {
                run.setId(UUID.randomUUID());
            }
            return run;
        });
        when(aiServiceGateway.queryRag(any(AiRagQueryRequest.class), any())).thenReturn(
                new AiRagQueryResponse(
                        "What is RAG?",
                        "RAG combines retrieval and generation.",
                        List.of(),
                        new AiTraceMetadata(
                                "trace-empty",
                                "ai-run-empty",
                                "rag_query",
                                "basic-rag",
                                "rag_answer",
                                "v1",
                                "stub-llm",
                                "completed",
                                5.0,
                                Map.of()
                        )
                )
        );

        RagQueryResponse response = ragService.query(new RagQueryRequest(
                null,
                null,
                null,
                "What is RAG?",
                null,
                null,
                null,
                null
        ));

        assertThat(response.status()).isEqualTo("COMPLETED");
        assertThat(response.citations()).isEmpty();
        verify(ragRetrievalResultRepository, never()).saveAll(any());
    }

    @Test
    void listRecentRunsReturnsClampedRunSummaries() {
        UUID runId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        RagRun run = new RagRun();
        run.setId(runId);
        run.setTraceId("trace-run");
        run.setKnowledgeBase(knowledgeBase);
        run.setQuestion("How does Advanced RAG rerank?");
        run.setStrategyName("advanced-rag");
        run.setRetrieverType("hybrid");
        run.setModelName("stub-llm");
        run.setLatencyMs(42L);
        run.setStatus("COMPLETED");

        when(ragRunRepository.findAllByOrderByCreatedAtDesc(PageRequest.of(0, 50))).thenReturn(List.of(run));

        List<RagRunSummaryResponse> responses = ragService.listRecentRuns(100);

        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).id()).isEqualTo(runId);
        assertThat(responses.get(0).knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(responses.get(0).strategyName()).isEqualTo("advanced-rag");
        assertThat(responses.get(0).status()).isEqualTo("COMPLETED");
    }
}
