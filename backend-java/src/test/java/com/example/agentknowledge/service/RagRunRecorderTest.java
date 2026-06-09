package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class RagRunRecorderTest {

    private final RagRunRepository ragRunRepository = mock(RagRunRepository.class);
    private final RagRetrievalResultRepository ragRetrievalResultRepository = mock(RagRetrievalResultRepository.class);
    private final DocumentChunkRepository documentChunkRepository = mock(DocumentChunkRepository.class);
    private final KnowledgeDocumentRepository knowledgeDocumentRepository = mock(KnowledgeDocumentRepository.class);

    private final RagRunRecorder recorder = new RagRunRecorder(
            ragRunRepository,
            ragRetrievalResultRepository,
            documentChunkRepository,
            knowledgeDocumentRepository
    );

    @Test
    void recordAgentRagRunStoresTracePayloadAndTopKResults() {
        ChatSession session = new ChatSession();
        session.setId(UUID.randomUUID());
        ChatMessage userMessage = new ChatMessage();
        userMessage.setId(UUID.randomUUID());
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(UUID.randomUUID());
        UUID documentId = UUID.randomUUID();
        UUID chunkId = UUID.randomUUID();

        when(ragRunRepository.save(any(RagRun.class))).thenAnswer(invocation -> {
            RagRun run = invocation.getArgument(0);
            run.setId(UUID.randomUUID());
            return run;
        });

        AiTraceMetadata agentTrace = new AiTraceMetadata(
                "trace-chat",
                "agent-run",
                "agent_invoke",
                "advanced-rag",
                "agent_invoke",
                "v1",
                "stub-llm",
                "completed",
                11.0,
                Map.of("rag_rewritten_query", "rag fine tuning compare"),
                List.of()
        );
        AiTraceMetadata ragTrace = new AiTraceMetadata(
                "trace-chat",
                "rag-run",
                "rag_query",
                "advanced-rag",
                "rag_answer",
                "v1",
                "stub-llm",
                "completed",
                9.0,
                Map.of("rewritten_query", "rag fine tuning compare"),
                List.of(Map.of("name", "query_rewrite", "status", "completed"))
        );

        recorder.recordAgentRagRun(
                session,
                userMessage,
                knowledgeBase,
                "rag和微调的区别",
                "answer",
                "advanced-rag",
                List.of(new AiSourceMetadata(
                        documentId,
                        chunkId,
                        "04-RAG与向量数据库",
                        "04-RAG与向量数据库.md",
                        0.47,
                        0.95,
                        null,
                        null,
                        Map.of("content_preview", "RAG 不改变模型参数，微调会改变模型参数。")
                )),
                agentTrace,
                ragTrace
        );

        ArgumentCaptor<RagRun> runCaptor = ArgumentCaptor.forClass(RagRun.class);
        verify(ragRunRepository).save(runCaptor.capture());
        RagRun run = runCaptor.getValue();
        assertThat(run.getTraceId()).isEqualTo("trace-chat");
        assertThat(run.getQuestion()).isEqualTo("rag和微调的区别");
        assertThat(run.getRewrittenQuery()).isEqualTo("rag fine tuning compare");
        assertThat(run.getTraceAttributes()).containsEntry("rewritten_query", "rag fine tuning compare");
        assertThat(run.getTraceAttributes()).containsEntry("rag_run_id", "rag-run");
        assertThat(run.getTraceSteps()).hasSize(1);
        assertThat(run.getFinalContext()).contains("RAG 不改变模型参数");

        ArgumentCaptor<List<RagRetrievalResult>> retrievalCaptor = ArgumentCaptor.forClass(List.class);
        verify(ragRetrievalResultRepository).saveAll(retrievalCaptor.capture());
        RagRetrievalResult retrievalResult = retrievalCaptor.getValue().getFirst();
        assertThat(retrievalResult.getRank()).isEqualTo(1);
        assertThat(retrievalResult.getScore()).isEqualTo(0.47);
        assertThat(retrievalResult.getRerankScore()).isEqualTo(0.95);
        assertThat(retrievalResult.getMetadata()).containsEntry(
                "content_preview",
                "RAG 不改变模型参数，微调会改变模型参数。"
        );
    }
}
