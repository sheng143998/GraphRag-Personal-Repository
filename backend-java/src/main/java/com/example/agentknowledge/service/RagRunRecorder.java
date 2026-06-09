package com.example.agentknowledge.service;

import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class RagRunRecorder {

    private final RagRunRepository ragRunRepository;
    private final RagRetrievalResultRepository ragRetrievalResultRepository;
    private final DocumentChunkRepository documentChunkRepository;
    private final KnowledgeDocumentRepository knowledgeDocumentRepository;

    public RagRunRecorder(
            RagRunRepository ragRunRepository,
            RagRetrievalResultRepository ragRetrievalResultRepository,
            DocumentChunkRepository documentChunkRepository,
            KnowledgeDocumentRepository knowledgeDocumentRepository
    ) {
        this.ragRunRepository = ragRunRepository;
        this.ragRetrievalResultRepository = ragRetrievalResultRepository;
        this.documentChunkRepository = documentChunkRepository;
        this.knowledgeDocumentRepository = knowledgeDocumentRepository;
    }

    public RagRun recordAgentRagRun(
            ChatSession session,
            ChatMessage userMessage,
            KnowledgeBase knowledgeBase,
            String question,
            String answer,
            String strategyName,
            List<AiSourceMetadata> citations,
            AiTraceMetadata agentTrace,
            AiTraceMetadata ragTrace
    ) {
        RagRun run = new RagRun();
        run.setTraceId(resolveTraceId(agentTrace, ragTrace));
        run.setSession(session);
        run.setMessage(userMessage);
        run.setKnowledgeBase(knowledgeBase);
        run.setQuestion(question);
        run.setRewrittenQuery(extractRewrittenQuery(agentTrace, ragTrace));
        run.setStrategyName(defaultString(strategyName, ragTrace == null ? null : ragTrace.strategyName()));
        run.setRetrieverType("hybrid");
        run.setFinalContext(buildFinalContext(citations));
        run.setAnswer(answer);
        run.setModelName(ragTrace == null ? null : ragTrace.modelName());
        run.setPromptName(ragTrace == null ? null : ragTrace.promptName());
        run.setPromptVersion(ragTrace == null ? null : ragTrace.promptVersion());
        run.setLatencyMs(toLongLatency(ragTrace == null ? null : ragTrace.latencyMs()));
        run.setTraceAttributes(traceAttributes(ragTrace));
        run.setTraceSteps(ragTrace == null || ragTrace.steps() == null ? List.of() : ragTrace.steps());
        run.setStatus("COMPLETED");
        run = ragRunRepository.save(run);
        saveRetrievalResults(run, citations);
        return run;
    }

    private String resolveTraceId(AiTraceMetadata agentTrace, AiTraceMetadata ragTrace) {
        if (ragTrace != null && ragTrace.traceId() != null && !ragTrace.traceId().isBlank()) {
            return ragTrace.traceId();
        }
        if (agentTrace != null && agentTrace.traceId() != null && !agentTrace.traceId().isBlank()) {
            return agentTrace.traceId();
        }
        String traceId = TraceContext.getTraceId();
        return traceId == null || traceId.isBlank() ? UUID.randomUUID().toString() : traceId;
    }

    private String extractRewrittenQuery(AiTraceMetadata agentTrace, AiTraceMetadata ragTrace) {
        Object value = null;
        if (ragTrace != null && ragTrace.attributes() != null) {
            value = ragTrace.attributes().get("rewritten_query");
        }
        if (value == null && agentTrace != null && agentTrace.attributes() != null) {
            value = agentTrace.attributes().get("rag_rewritten_query");
        }
        return value == null ? null : Objects.toString(value, null);
    }

    private Map<String, Object> traceAttributes(AiTraceMetadata ragTrace) {
        if (ragTrace == null) {
            return Collections.emptyMap();
        }
        Map<String, Object> attributes = new HashMap<>(
                ragTrace.attributes() == null ? Collections.emptyMap() : ragTrace.attributes()
        );
        if (ragTrace.runId() != null && !ragTrace.runId().isBlank()) {
            attributes.putIfAbsent("rag_run_id", ragTrace.runId());
        }
        return attributes;
    }

    private void saveRetrievalResults(RagRun run, List<AiSourceMetadata> citations) {
        if (citations == null || citations.isEmpty()) {
            return;
        }
        List<RagRetrievalResult> results = new ArrayList<>();
        int rank = 1;
        for (AiSourceMetadata citation : citations) {
            if (citation == null) {
                continue;
            }
            results.add(toRetrievalResult(run, citation, rank));
            rank++;
        }
        if (!results.isEmpty()) {
            ragRetrievalResultRepository.saveAll(results);
        }
    }

    private RagRetrievalResult toRetrievalResult(RagRun run, AiSourceMetadata citation, int rank) {
        RagRetrievalResult result = new RagRetrievalResult();
        result.setRun(run);
        result.setRank(rank);
        result.setScore(citation.score());
        result.setRerankScore(citation.rerankScore());
        result.setRetrieverType("hybrid");
        result.setSource(citation.title());
        result.setSelectedForContext(Boolean.TRUE);
        result.setMetadata(citation.metadata() == null ? Collections.emptyMap() : citation.metadata());
        if (citation.chunkId() != null) {
            documentChunkRepository.findById(citation.chunkId()).ifPresent(result::setChunk);
        }
        if (citation.documentId() != null) {
            knowledgeDocumentRepository.findById(citation.documentId()).ifPresent(result::setDocument);
        }
        return result;
    }

    private String buildFinalContext(List<AiSourceMetadata> citations) {
        if (citations == null) {
            return "";
        }
        return citations.stream()
                .filter(Objects::nonNull)
                .map(citation -> citation.metadata() == null ? null : Objects.toString(citation.metadata().get("content_preview"), null))
                .filter(Objects::nonNull)
                .filter(value -> !value.isBlank())
                .toList()
                .stream()
                .reduce((left, right) -> left + "\n\n" + right)
                .orElse("");
    }

    private String defaultString(String value, String fallback) {
        return value != null && !value.isBlank() ? value : fallback;
    }

    private Long toLongLatency(Double latencyMs) {
        return latencyMs == null ? null : Math.round(latencyMs);
    }
}
