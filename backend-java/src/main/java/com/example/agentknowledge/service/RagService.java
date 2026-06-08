package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagQueryRequest;
import com.example.agentknowledge.client.dto.AiRagQueryResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.DocumentChunk;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.RagQueryRequest;
import com.example.agentknowledge.dto.rag.RagQueryResponse;
import com.example.agentknowledge.dto.rag.RagRunResponse;
import com.example.agentknowledge.dto.rag.RagRunSummaryResponse;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

@Service
public class RagService {

    private final RagRunRepository ragRunRepository;
    private final RagRetrievalResultRepository ragRetrievalResultRepository;
    private final KnowledgeBaseService knowledgeBaseService;
    private final ChatService chatService;
    private final AiServiceGateway aiServiceGateway;
    private final DocumentChunkRepository documentChunkRepository;
    private final KnowledgeDocumentRepository knowledgeDocumentRepository;

    public RagService(
            RagRunRepository ragRunRepository,
            RagRetrievalResultRepository ragRetrievalResultRepository,
            KnowledgeBaseService knowledgeBaseService,
            ChatService chatService,
            AiServiceGateway aiServiceGateway,
            DocumentChunkRepository documentChunkRepository,
            KnowledgeDocumentRepository knowledgeDocumentRepository
    ) {
        this.ragRunRepository = ragRunRepository;
        this.ragRetrievalResultRepository = ragRetrievalResultRepository;
        this.knowledgeBaseService = knowledgeBaseService;
        this.chatService = chatService;
        this.aiServiceGateway = aiServiceGateway;
        this.documentChunkRepository = documentChunkRepository;
        this.knowledgeDocumentRepository = knowledgeDocumentRepository;
    }

    public RagQueryResponse query(RagQueryRequest request) {
        String strategyName = request.strategyName() == null || request.strategyName().isBlank()
                ? "basic-rag"
                : request.strategyName();
        String retrieverType = request.retrieverType() == null || request.retrieverType().isBlank()
                ? "hybrid"
                : request.retrieverType();
        RagRun run = new RagRun();
        run.setTraceId(TraceContext.getTraceId());
        run.setQuestion(request.question());
        run.setStrategyName(strategyName);
        run.setRetrieverType(retrieverType);
        run.setStatus("PENDING");

        if (request.knowledgeBaseId() != null) {
            KnowledgeBase knowledgeBase = knowledgeBaseService.getReference(request.knowledgeBaseId());
            run.setKnowledgeBase(knowledgeBase);
        }
        if (request.sessionId() != null) {
            ChatSession session = chatService.getSession(request.sessionId());
            run.setSession(session);
        }
        if (request.messageId() != null) {
            ChatMessage message = chatService.getMessage(request.messageId());
            run.setMessage(message);
        }

        run = ragRunRepository.save(run);

        try {
            AiRagQueryResponse aiResponse = aiServiceGateway.queryRag(new AiRagQueryRequest(
                    request.question(),
                    request.topK() == null ? 5 : request.topK(),
                    strategyName,
                    new AiRagQueryRequest.Context(
                            request.knowledgeBaseId(),
                            request.sessionId(),
                            request.messageId(),
                            request.metadataFilters() == null ? Collections.emptyMap() : request.metadataFilters(),
                            request.retrievalOptions() == null ? Collections.emptyMap() : request.retrievalOptions()
                    )
            ), TraceContext.getTraceId());

            run.setStatus("COMPLETED");
            run.setAnswer(aiResponse.answer());
            run.setModelName(aiResponse.trace() == null ? null : aiResponse.trace().modelName());
            run.setPromptName(aiResponse.trace() == null ? null : aiResponse.trace().promptName());
            run.setPromptVersion(aiResponse.trace() == null ? null : aiResponse.trace().promptVersion());
            run.setLatencyMs(toLongLatency(aiResponse.trace() == null ? null : aiResponse.trace().latencyMs()));
            run.setRewrittenQuery(extractRewrittenQuery(aiResponse));
            run.setFinalContext(buildFinalContext(aiResponse.citations()));
            run = ragRunRepository.save(run);
            saveRetrievalResults(run, aiResponse.citations(), retrieverType);

            return new RagQueryResponse(
                    run.getId(),
                    run.getTraceId(),
                    run.getStatus(),
                    aiResponse.answer(),
                    toCitationLabels(aiResponse.citations()),
                    strategyName,
                    retrieverType
            );
        } catch (RuntimeException exception) {
            run.setStatus("FAILED");
            run.setErrorMessage(exception.getMessage());
            ragRunRepository.save(run);
            throw exception;
        }
    }

    public RagRunResponse getRun(UUID runId) {
        RagRun run = getRunEntity(runId);
        List<RagRunResponse.RetrievalResultResponse> retrievalResults = ragRetrievalResultRepository.findByRunIdOrderByRankAsc(runId)
                .stream()
                .map(this::toRetrievalResultResponse)
                .toList();

        return new RagRunResponse(
                run.getId(),
                run.getTraceId(),
                run.getSession() == null ? null : run.getSession().getId(),
                run.getMessage() == null ? null : run.getMessage().getId(),
                run.getKnowledgeBase() == null ? null : run.getKnowledgeBase().getId(),
                run.getQuestion(),
                run.getRewrittenQuery(),
                run.getStrategyName(),
                run.getRetrieverType(),
                run.getFinalContext(),
                run.getAnswer(),
                run.getModelName(),
                run.getPromptName(),
                run.getPromptVersion(),
                run.getLatencyMs(),
                run.getStatus(),
                run.getErrorMessage(),
                run.getCreatedAt(),
                retrievalResults
        );
    }

    public List<RagRunSummaryResponse> listRecentRuns(Integer limit) {
        int pageSize = limit == null ? 20 : Math.max(1, Math.min(limit, 50));
        return ragRunRepository.findAllByOrderByCreatedAtDesc(PageRequest.of(0, pageSize))
                .stream()
                .map(this::toRunSummaryResponse)
                .toList();
    }

    public RagRun getRunEntity(UUID runId) {
        return ragRunRepository.findById(runId)
                .orElseThrow(() -> new ResourceNotFoundException("RAG run not found: " + runId));
    }

    private void saveRetrievalResults(RagRun run, List<AiSourceMetadata> citations, String retrieverType) {
        if (citations == null || citations.isEmpty()) {
            return;
        }
        List<RagRetrievalResult> results = new java.util.ArrayList<>();
        int rank = 1;
        for (AiSourceMetadata citation : citations) {
            if (citation == null) {
                continue;
            }
            results.add(toRetrievalResult(run, citation, retrieverType, rank));
            rank++;
        }
        ragRetrievalResultRepository.saveAll(results);
    }

    private RagRetrievalResult toRetrievalResult(
            RagRun run,
            AiSourceMetadata citation,
            String retrieverType,
            int rank
    ) {
        RagRetrievalResult result = new RagRetrievalResult();
        result.setRun(run);
        result.setRank(rank);
        result.setScore(citation.score());
        result.setRerankScore(citation.rerankScore());
        result.setRetrieverType(retrieverType);
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

    private List<String> toCitationLabels(List<AiSourceMetadata> citations) {
        if (citations == null) {
            return List.of();
        }
        return citations.stream()
                .filter(Objects::nonNull)
                .map(citation -> {
                    String preview = citation.metadata() == null ? null : Objects.toString(citation.metadata().get("content_preview"), null);
                    return citation.title() + (preview == null || preview.isBlank() ? "" : " | " + preview);
                })
                .toList();
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

    private String extractRewrittenQuery(AiRagQueryResponse aiResponse) {
        if (aiResponse.trace() == null || aiResponse.trace().attributes() == null) {
            return null;
        }
        Object rewrittenQuery = aiResponse.trace().attributes().get("rewritten_query");
        return rewrittenQuery == null ? null : Objects.toString(rewrittenQuery, null);
    }

    private Long toLongLatency(Double latencyMs) {
        return latencyMs == null ? null : Math.round(latencyMs);
    }

    private RagRunSummaryResponse toRunSummaryResponse(RagRun run) {
        return new RagRunSummaryResponse(
                run.getId(),
                run.getTraceId(),
                run.getSession() == null ? null : run.getSession().getId(),
                run.getMessage() == null ? null : run.getMessage().getId(),
                run.getKnowledgeBase() == null ? null : run.getKnowledgeBase().getId(),
                run.getQuestion(),
                run.getStrategyName(),
                run.getRetrieverType(),
                run.getModelName(),
                run.getLatencyMs(),
                run.getStatus(),
                run.getCreatedAt()
        );
    }

    private RagRunResponse.RetrievalResultResponse toRetrievalResultResponse(RagRetrievalResult result) {
        return new RagRunResponse.RetrievalResultResponse(
                result.getId(),
                result.getChunk() == null ? null : result.getChunk().getId(),
                result.getDocument() == null ? null : result.getDocument().getId(),
                result.getRank(),
                result.getScore(),
                result.getRerankScore(),
                result.getRetrieverType(),
                result.getSource(),
                result.getMetadata(),
                result.getSelectedForContext()
        );
    }
}
