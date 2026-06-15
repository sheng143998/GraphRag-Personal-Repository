package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagEvaluateRequest;
import com.example.agentknowledge.client.dto.AiRagEvaluateResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.RagEvaluationCase;
import com.example.agentknowledge.domain.RagExperiment;
import com.example.agentknowledge.domain.RagExperimentEvaluation;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.CreateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.CreateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.RagEvaluationCaseResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationHistoryResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationSummaryResponse;
import com.example.agentknowledge.dto.rag.RagExperimentResponse;
import com.example.agentknowledge.dto.rag.RagQueryRequest;
import com.example.agentknowledge.dto.rag.RagQueryResponse;
import com.example.agentknowledge.dto.rag.RunEvaluationCasesBatchRequest;
import com.example.agentknowledge.dto.rag.RunEvaluationCasesBatchResponse;
import com.example.agentknowledge.dto.rag.UpdateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.UpdateRagExperimentRequest;
import com.example.agentknowledge.repository.RagEvaluationCaseRepository;
import com.example.agentknowledge.repository.RagExperimentRepository;
import com.example.agentknowledge.repository.RagExperimentEvaluationRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RagExperimentService {

    private final RagExperimentRepository ragExperimentRepository;
    private final RagEvaluationCaseRepository ragEvaluationCaseRepository;
    private final RagExperimentEvaluationRepository ragExperimentEvaluationRepository;
    private final RagRunRepository ragRunRepository;
    private final RagRetrievalResultRepository ragRetrievalResultRepository;
    private final KnowledgeBaseService knowledgeBaseService;
    private final AiServiceGateway aiServiceGateway;
    private final RagService ragService;

    public RagExperimentService(
            RagExperimentRepository ragExperimentRepository,
            RagEvaluationCaseRepository ragEvaluationCaseRepository,
            RagExperimentEvaluationRepository ragExperimentEvaluationRepository,
            RagRunRepository ragRunRepository,
            RagRetrievalResultRepository ragRetrievalResultRepository,
            KnowledgeBaseService knowledgeBaseService,
            AiServiceGateway aiServiceGateway,
            RagService ragService
    ) {
        this.ragExperimentRepository = ragExperimentRepository;
        this.ragEvaluationCaseRepository = ragEvaluationCaseRepository;
        this.ragExperimentEvaluationRepository = ragExperimentEvaluationRepository;
        this.ragRunRepository = ragRunRepository;
        this.ragRetrievalResultRepository = ragRetrievalResultRepository;
        this.knowledgeBaseService = knowledgeBaseService;
        this.aiServiceGateway = aiServiceGateway;
        this.ragService = ragService;
    }

    public RagExperimentResponse create(CreateRagExperimentRequest request) {
        RagExperiment experiment = new RagExperiment();
        if (request.knowledgeBaseId() != null) {
            experiment.setKnowledgeBase(knowledgeBaseService.getReference(request.knowledgeBaseId()));
        }
        experiment.setName(request.name());
        experiment.setDescription(request.description());
        experiment.setStrategyName(request.strategy());
        experiment.setDatasetName(request.datasetName());
        experiment.setSampleCount(request.sampleCount());
        experiment.setPrecisionScore(request.precisionScore());
        experiment.setRecallScore(request.recallScore());
        experiment.setStatus(normalizeStatus(request.status()));
        experiment.setNotes(request.notes());
        return toResponse(ragExperimentRepository.save(experiment));
    }

    public List<RagExperimentResponse> list() {
        return ragExperimentRepository.findAllByOrderByUpdatedAtDesc()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    public RagExperimentResponse get(UUID id) {
        return toResponse(getEntity(id));
    }

    public List<RagEvaluationCaseResponse> listEvaluationCases(UUID experimentId) {
        List<RagEvaluationCase> cases = experimentId == null
                ? ragEvaluationCaseRepository.findAllByOrderByUpdatedAtDesc()
                : ragEvaluationCaseRepository.findByExperiment_IdOrderByUpdatedAtDesc(experimentId);
        return cases.stream().map(this::toEvaluationCaseResponse).toList();
    }

    public RagEvaluationCaseResponse createEvaluationCase(CreateRagEvaluationCaseRequest request) {
        RagEvaluationCase evaluationCase = new RagEvaluationCase();
        evaluationCase.setExperiment(getEntity(request.experimentId()));
        evaluationCase.setCaseId(request.caseId());
        evaluationCase.setQuestion(request.question());
        evaluationCase.setExpectedAnswer(request.expectedAnswer());
        evaluationCase.setRelevantChunkIds(emptyIfNull(request.relevantChunkIds()));
        evaluationCase.setRelevantDocumentIds(emptyIfNull(request.relevantDocumentIds()));
        evaluationCase.setExpectedCitationChunkIds(emptyIfNull(request.expectedCitationChunkIds()));
        evaluationCase.setEvaluationTopK(request.evaluationTopK() == null ? 5 : Math.max(1, request.evaluationTopK()));
        evaluationCase.setNotes(request.notes());
        evaluationCase.setStatus(normalizeCaseStatus(request.status()));
        return toEvaluationCaseResponse(ragEvaluationCaseRepository.save(evaluationCase));
    }

    public RagEvaluationCaseResponse updateEvaluationCase(UUID id, UpdateRagEvaluationCaseRequest request) {
        RagEvaluationCase evaluationCase = getEvaluationCaseEntity(id);
        if (request.experimentId() != null) {
            evaluationCase.setExperiment(getEntity(request.experimentId()));
        }
        if (hasText(request.caseId())) {
            evaluationCase.setCaseId(request.caseId());
        }
        if (hasText(request.question())) {
            evaluationCase.setQuestion(request.question());
        }
        if (request.expectedAnswer() != null) {
            evaluationCase.setExpectedAnswer(request.expectedAnswer());
        }
        if (request.relevantChunkIds() != null) {
            evaluationCase.setRelevantChunkIds(request.relevantChunkIds());
        }
        if (request.relevantDocumentIds() != null) {
            evaluationCase.setRelevantDocumentIds(request.relevantDocumentIds());
        }
        if (request.expectedCitationChunkIds() != null) {
            evaluationCase.setExpectedCitationChunkIds(request.expectedCitationChunkIds());
        }
        if (request.evaluationTopK() != null) {
            evaluationCase.setEvaluationTopK(Math.max(1, request.evaluationTopK()));
        }
        if (request.notes() != null) {
            evaluationCase.setNotes(request.notes());
        }
        if (hasText(request.status())) {
            evaluationCase.setStatus(request.status());
        }
        return toEvaluationCaseResponse(ragEvaluationCaseRepository.save(evaluationCase));
    }

    public void deleteEvaluationCase(UUID id) {
        ragEvaluationCaseRepository.delete(getEvaluationCaseEntity(id));
    }

    @Transactional
    public RagExperimentEvaluationResponse evaluateCase(UUID caseId, EvaluateRagEvaluationCaseRequest request) {
        RagEvaluationCase evaluationCase = getEvaluationCaseEntity(caseId);
        String expectedAnswer = hasText(request.expectedAnswer())
                ? request.expectedAnswer()
                : evaluationCase.getExpectedAnswer();
        return evaluate(
                evaluationCase.getExperiment().getId(),
                new EvaluateRagExperimentRequest(
                        request.runId(),
                        expectedAnswer,
                        evaluationCase.getCaseId(),
                        evaluationCase.getRelevantChunkIds(),
                        evaluationCase.getRelevantDocumentIds(),
                        evaluationCase.getExpectedCitationChunkIds(),
                        evaluationCase.getEvaluationTopK()
                )
        );
    }

    @Transactional
    public RunEvaluationCasesBatchResponse runBatch(RunEvaluationCasesBatchRequest request) {
        RagExperiment experiment = getEntity(request.experimentId());
        if (experiment.getKnowledgeBase() == null) {
            throw new IllegalArgumentException("Experiment must be linked to a knowledge base before running evaluation cases.");
        }
        List<RagEvaluationCase> cases = selectedEvaluationCases(request);
        String strategyName = hasText(request.strategyName()) ? request.strategyName() : experiment.getStrategyName();
        String retrieverType = hasText(request.retrieverType()) ? request.retrieverType() : "hybrid";
        Integer topK = request.topK() == null ? 5 : Math.max(1, request.topK());
        List<RunEvaluationCasesBatchResponse.Item> items = cases.stream()
                .map(evaluationCase -> runAndEvaluateCase(
                        experiment,
                        evaluationCase,
                        strategyName,
                        retrieverType,
                        topK,
                        request.metadataFilters(),
                        request.retrievalOptions()
                ))
                .toList();
        int completed = (int) items.stream().filter(item -> "COMPLETED".equals(item.status())).count();
        return new RunEvaluationCasesBatchResponse(
                experiment.getId(),
                strategyName,
                items.size(),
                completed,
                items.size() - completed,
                items
        );
    }

    public RagExperimentEvaluationSummaryResponse summarizeEvaluations(Integer limit) {
        List<RagExperimentEvaluation> evaluations = ragExperimentEvaluationRepository
                .findAllByOrderByCreatedAtDesc(PageRequest.of(0, normalizeLimit(limit)));
        List<RagExperimentEvaluationHistoryResponse> recent = evaluations.stream()
                .map(this::toEvaluationHistoryResponse)
                .toList();
        RagExperimentEvaluation best = evaluations.stream()
                .filter(item -> item.getGroundedScore() != null || item.getRetrievalScore() != null)
                .max((left, right) -> Double.compare(evaluationQuality(left), evaluationQuality(right)))
                .orElse(null);

        return new RagExperimentEvaluationSummaryResponse(
                evaluations.size(),
                average(evaluations.stream().map(RagExperimentEvaluation::getGroundedScore).toList()),
                average(evaluations.stream().map(RagExperimentEvaluation::getRetrievalScore).toList()),
                best == null || best.getExperiment() == null ? null : best.getExperiment().getId(),
                best == null || best.getExperiment() == null ? null : best.getExperiment().getName(),
                recent
        );
    }

    public RagExperimentResponse update(UUID id, UpdateRagExperimentRequest request) {
        RagExperiment experiment = getEntity(id);
        if (request.knowledgeBaseId() != null) {
            experiment.setKnowledgeBase(knowledgeBaseService.getReference(request.knowledgeBaseId()));
        }
        if (hasText(request.name())) {
            experiment.setName(request.name());
        }
        if (request.description() != null) {
            experiment.setDescription(request.description());
        }
        if (hasText(request.strategy())) {
            experiment.setStrategyName(request.strategy());
        }
        if (request.datasetName() != null) {
            experiment.setDatasetName(request.datasetName());
        }
        if (request.sampleCount() != null) {
            experiment.setSampleCount(request.sampleCount());
        }
        if (request.precisionScore() != null) {
            experiment.setPrecisionScore(request.precisionScore());
        }
        if (request.recallScore() != null) {
            experiment.setRecallScore(request.recallScore());
        }
        if (hasText(request.status())) {
            experiment.setStatus(request.status());
        }
        if (request.notes() != null) {
            experiment.setNotes(request.notes());
        }
        return toResponse(ragExperimentRepository.save(experiment));
    }

    @Transactional
    public RagExperimentEvaluationResponse evaluate(UUID id, EvaluateRagExperimentRequest request) {
        RagExperiment experiment = getEntity(id);
        RagRun run = ragRunRepository.findById(request.runId())
                .orElseThrow(() -> new ResourceNotFoundException("RAG run not found: " + request.runId()));
        List<RagRetrievalResult> retrievalResults = ragRetrievalResultRepository.findByRunIdOrderByRankAsc(run.getId());
        AiRagEvaluateResponse evaluation = aiServiceGateway.evaluateRag(
                new AiRagEvaluateRequest(
                        run.getQuestion(),
                        request.expectedAnswer(),
                        run.getAnswer(),
                        retrievalResults.stream().map(this::toAiSource).toList(),
                        run.getStrategyName() != null ? run.getStrategyName() : experiment.getStrategyName(),
                        new AiRagEvaluateRequest.Context(
                                run.getKnowledgeBase() == null ? null : run.getKnowledgeBase().getId(),
                                run.getSession() == null ? null : run.getSession().getId(),
                                run.getMessage() == null ? null : run.getMessage().getId(),
                                Map.of()
                        ),
                        toEvaluationCase(request)
                ),
                TraceContext.getTraceId()
        );

        AiRagEvaluateResponse.Result result = evaluation.result();
        Double groundedScore = result == null ? null : result.groundedScore();
        Double retrievalScore = result == null ? null : result.retrievalScore();
        List<String> notes = result == null || result.notes() == null
                ? List.of()
                : result.notes();
        experiment.setPrecisionScore(groundedScore);
        experiment.setRecallScore(retrievalScore);
        experiment.setSampleCount(experiment.getSampleCount() == null || experiment.getSampleCount() == 0
                ? 1
                : experiment.getSampleCount());
        experiment.setStatus("COMPLETED");
        experiment.setNotes(formatEvaluationNotes(experiment.getNotes(), run.getId(), notes));
        RagExperiment savedExperiment = ragExperimentRepository.save(experiment);
        RagExperimentEvaluation savedEvaluation = saveEvaluationHistory(
                savedExperiment,
                run,
                request.expectedAnswer(),
                result,
                notes
        );
        RagExperimentResponse updated = toResponse(savedExperiment);
        return new RagExperimentEvaluationResponse(
                updated,
                toEvaluationHistoryResponse(savedEvaluation),
                groundedScore,
                retrievalScore,
                result == null ? null : result.recallAtK(),
                result == null ? null : result.precisionAtK(),
                result == null ? null : result.mrr(),
                result == null ? null : result.citationHit(),
                notes,
                updated.evaluations()
        );
    }

    public void delete(UUID id) {
        ragExperimentRepository.delete(getEntity(id));
    }

    private RagExperimentResponse toResponse(RagExperiment experiment) {
        return new RagExperimentResponse(
                experiment.getId(),
                experiment.getKnowledgeBase() == null ? null : experiment.getKnowledgeBase().getId(),
                experiment.getName(),
                experiment.getDescription(),
                experiment.getStrategyName(),
                experiment.getDatasetName(),
                experiment.getSampleCount(),
                experiment.getPrecisionScore(),
                experiment.getRecallScore(),
                formatMetric(experiment.getPrecisionScore()),
                formatMetric(experiment.getRecallScore()),
                experiment.getStatus(),
                experiment.getNotes(),
                experiment.getCreatedAt(),
                experiment.getUpdatedAt(),
                listEvaluationHistory(experiment.getId())
        );
    }

    private String normalizeStatus(String status) {
        return status == null || status.isBlank() ? "PLANNED" : status;
    }

    private String normalizeCaseStatus(String status) {
        return status == null || status.isBlank() ? "ACTIVE" : status;
    }

    private RagExperiment getEntity(UUID id) {
        return ragExperimentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("RAG experiment not found: " + id));
    }

    private RagEvaluationCase getEvaluationCaseEntity(UUID id) {
        return ragEvaluationCaseRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("RAG evaluation case not found: " + id));
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private List<RagEvaluationCase> selectedEvaluationCases(RunEvaluationCasesBatchRequest request) {
        List<RagEvaluationCase> cases = ragEvaluationCaseRepository
                .findByExperiment_IdOrderByUpdatedAtDesc(request.experimentId())
                .stream()
                .filter(item -> "ACTIVE".equalsIgnoreCase(item.getStatus()))
                .toList();
        if (request.caseIds() == null || request.caseIds().isEmpty()) {
            return cases;
        }
        Set<UUID> requestedIds = Set.copyOf(request.caseIds());
        return cases.stream()
                .filter(item -> requestedIds.contains(item.getId()))
                .toList();
    }

    private RunEvaluationCasesBatchResponse.Item runAndEvaluateCase(
            RagExperiment experiment,
            RagEvaluationCase evaluationCase,
            String strategyName,
            String retrieverType,
            Integer topK,
            Map<String, Object> metadataFilters,
            Map<String, Object> retrievalOptions
    ) {
        try {
            RagQueryResponse queryResponse = ragService.query(new RagQueryRequest(
                    experiment.getKnowledgeBase() == null ? null : experiment.getKnowledgeBase().getId(),
                    null,
                    null,
                    evaluationCase.getQuestion(),
                    strategyName,
                    retrieverType,
                    metadataFilters == null ? Map.of() : metadataFilters,
                    retrievalOptions == null ? Map.of() : retrievalOptions,
                    topK
            ));
            RagExperimentEvaluationResponse evaluation = evaluateCase(
                    evaluationCase.getId(),
                    new EvaluateRagEvaluationCaseRequest(
                            queryResponse.runId(),
                            evaluationCase.getExpectedAnswer()
                    )
            );
            RagExperimentEvaluationHistoryResponse history = evaluation.evaluation();
            return new RunEvaluationCasesBatchResponse.Item(
                    evaluationCase.getId(),
                    evaluationCase.getCaseId(),
                    queryResponse.runId(),
                    history == null ? null : history.id(),
                    evaluation.groundedScore(),
                    evaluation.retrievalScore(),
                    evaluation.recallAtK(),
                    evaluation.precisionAtK(),
                    evaluation.mrr(),
                    evaluation.citationHit(),
                    "COMPLETED",
                    null
            );
        } catch (RuntimeException exception) {
            return new RunEvaluationCasesBatchResponse.Item(
                    evaluationCase.getId(),
                    evaluationCase.getCaseId(),
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    "FAILED",
                    exception.getMessage()
            );
        }
    }

    private String formatMetric(Double value) {
        return value == null ? "pending" : String.format(Locale.ROOT, "%.2f", value);
    }

    private int normalizeLimit(Integer limit) {
        if (limit == null) {
            return 20;
        }
        return Math.max(1, Math.min(limit, 50));
    }

    private List<UUID> emptyIfNull(List<UUID> values) {
        return values == null ? List.of() : values;
    }

    private Double average(List<Double> values) {
        List<Double> valid = values.stream()
                .filter(value -> value != null)
                .toList();
        if (valid.isEmpty()) {
            return null;
        }
        return valid.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
    }

    private double evaluationQuality(RagExperimentEvaluation evaluation) {
        Double grounded = evaluation.getGroundedScore();
        Double retrieval = evaluation.getRetrievalScore();
        if (grounded != null && retrieval != null) {
            return (grounded + retrieval) / 2.0;
        }
        if (grounded != null) {
            return grounded;
        }
        return retrieval == null ? 0.0 : retrieval;
    }

    private AiSourceMetadata toAiSource(RagRetrievalResult result) {
        return new AiSourceMetadata(
                result.getDocument() == null ? null : result.getDocument().getId(),
                result.getChunk() == null ? null : result.getChunk().getId(),
                result.getSource(),
                null,
                result.getScore(),
                result.getRerankScore(),
                null,
                null,
                result.getMetadata()
        );
    }

    private AiRagEvaluateRequest.EvaluationCase toEvaluationCase(EvaluateRagExperimentRequest request) {
        if (
                !hasText(request.evaluationCaseId())
                        && isEmpty(request.relevantChunkIds())
                        && isEmpty(request.relevantDocumentIds())
                        && isEmpty(request.expectedCitationChunkIds())
        ) {
            return null;
        }
        return new AiRagEvaluateRequest.EvaluationCase(
                hasText(request.evaluationCaseId()) ? request.evaluationCaseId() : request.runId().toString(),
                request.relevantChunkIds() == null ? List.of() : request.relevantChunkIds(),
                request.relevantDocumentIds() == null ? List.of() : request.relevantDocumentIds(),
                request.expectedCitationChunkIds() == null ? List.of() : request.expectedCitationChunkIds(),
                request.evaluationTopK() == null ? 5 : Math.max(1, request.evaluationTopK())
        );
    }

    private boolean isEmpty(List<?> values) {
        return values == null || values.isEmpty();
    }

    private RagEvaluationCaseResponse toEvaluationCaseResponse(RagEvaluationCase evaluationCase) {
        RagExperiment experiment = evaluationCase.getExperiment();
        return new RagEvaluationCaseResponse(
                evaluationCase.getId(),
                experiment == null ? null : experiment.getId(),
                experiment == null ? null : experiment.getName(),
                evaluationCase.getCaseId(),
                evaluationCase.getQuestion(),
                evaluationCase.getExpectedAnswer(),
                evaluationCase.getRelevantChunkIds(),
                evaluationCase.getRelevantDocumentIds(),
                evaluationCase.getExpectedCitationChunkIds(),
                evaluationCase.getEvaluationTopK(),
                evaluationCase.getNotes(),
                evaluationCase.getStatus(),
                evaluationCase.getCreatedAt(),
                evaluationCase.getUpdatedAt()
        );
    }

    private RagExperimentEvaluation saveEvaluationHistory(
            RagExperiment experiment,
            RagRun run,
            String expectedAnswer,
            AiRagEvaluateResponse.Result result,
            List<String> notes
    ) {
        RagExperimentEvaluation evaluation = new RagExperimentEvaluation();
        evaluation.setExperiment(experiment);
        evaluation.setRun(run);
        evaluation.setGroundedScore(result == null ? null : result.groundedScore());
        evaluation.setRetrievalScore(result == null ? null : result.retrievalScore());
        evaluation.setRecallAtK(result == null ? null : result.recallAtK());
        evaluation.setPrecisionAtK(result == null ? null : result.precisionAtK());
        evaluation.setMrr(result == null ? null : result.mrr());
        evaluation.setCitationHit(result == null ? null : result.citationHit());
        evaluation.setGraphEntityCoverage(result == null ? null : result.graphEntityCoverage());
        evaluation.setGraphRelationshipHit(result == null ? null : result.graphRelationshipHit());
        evaluation.setGraphExpansionTermHit(result == null ? null : result.graphExpansionTermHit());
        evaluation.setLatencyMs(run.getLatencyMs());
        EvaluationCostSnapshot costSnapshot = extractCostSnapshot(run);
        evaluation.setPromptTokens(costSnapshot.promptTokens());
        evaluation.setCompletionTokens(costSnapshot.completionTokens());
        evaluation.setTotalTokens(costSnapshot.totalTokens());
        evaluation.setEmbeddingTokens(costSnapshot.embeddingTokens());
        evaluation.setRerankTokens(costSnapshot.rerankTokens());
        evaluation.setEstimatedCost(costSnapshot.estimatedCost());
        evaluation.setEmbeddingLatencyMs(costSnapshot.embeddingLatencyMs());
        evaluation.setRetrievalLatencyMs(costSnapshot.retrievalLatencyMs());
        evaluation.setRerankLatencyMs(costSnapshot.rerankLatencyMs());
        evaluation.setLlmLatencyMs(costSnapshot.llmLatencyMs());
        evaluation.setTokenUsage(costSnapshot.tokenUsage());
        evaluation.setLatencyBreakdown(costSnapshot.latencyBreakdown());
        evaluation.setStrategyConfig(strategyConfigSnapshot(run));
        evaluation.setExpectedAnswer(expectedAnswer);
        evaluation.setGeneratedAnswer(run.getAnswer());
        evaluation.setNotes(String.join("\n", notes));
        return ragExperimentEvaluationRepository.save(evaluation);
    }

    private List<RagExperimentEvaluationHistoryResponse> listEvaluationHistory(UUID experimentId) {
        if (experimentId == null) {
            return List.of();
        }
        return ragExperimentEvaluationRepository
                .findByExperiment_IdOrderByCreatedAtDesc(experimentId, PageRequest.of(0, 5))
                .stream()
                .map(this::toEvaluationHistoryResponse)
                .toList();
    }

    private RagExperimentEvaluationHistoryResponse toEvaluationHistoryResponse(RagExperimentEvaluation evaluation) {
        RagRun run = evaluation.getRun();
        return new RagExperimentEvaluationHistoryResponse(
                evaluation.getId(),
                evaluation.getExperiment().getId(),
                evaluation.getExperiment().getName(),
                run.getId(),
                run.getQuestion(),
                run.getStrategyName(),
                run.getRetrieverType(),
                run.getModelName(),
                run.getLatencyMs(),
                run.getCreatedAt(),
                evaluation.getGroundedScore(),
                evaluation.getRetrievalScore(),
                evaluation.getRecallAtK(),
                evaluation.getPrecisionAtK(),
                evaluation.getMrr(),
                evaluation.getCitationHit(),
                evaluation.getGraphEntityCoverage(),
                evaluation.getGraphRelationshipHit(),
                evaluation.getGraphExpansionTermHit(),
                evaluation.getLatencyMs(),
                evaluation.getPromptTokens(),
                evaluation.getCompletionTokens(),
                evaluation.getTotalTokens(),
                evaluation.getEmbeddingTokens(),
                evaluation.getRerankTokens(),
                evaluation.getEstimatedCost(),
                evaluation.getEmbeddingLatencyMs(),
                evaluation.getRetrievalLatencyMs(),
                evaluation.getRerankLatencyMs(),
                evaluation.getLlmLatencyMs(),
                evaluation.getTokenUsage(),
                evaluation.getLatencyBreakdown(),
                evaluation.getStrategyConfig(),
                evaluation.getExpectedAnswer(),
                evaluation.getGeneratedAnswer(),
                evaluation.getNotes(),
                evaluation.getCreatedAt()
        );
    }

    private String formatEvaluationNotes(String existingNotes, UUID runId, List<String> notes) {
        String evaluationLine = "Evaluation run " + runId + ": " + String.join(" ", notes);
        if (existingNotes == null || existingNotes.isBlank()) {
            return evaluationLine;
        }
        return existingNotes + "\n" + evaluationLine;
    }

    private Map<String, Object> strategyConfigSnapshot(RagRun run) {
        Map<String, Object> values = new LinkedHashMap<>();
        putIfPresent(values, "strategyName", run.getStrategyName());
        putIfPresent(values, "retrieverType", run.getRetrieverType());
        putIfPresent(values, "modelName", run.getModelName());
        putIfPresent(values, "promptName", run.getPromptName());
        putIfPresent(values, "promptVersion", run.getPromptVersion());
        Map<String, Object> attributes = run.getTraceAttributes() == null ? Map.of() : run.getTraceAttributes();
        putIfPresent(values, "ragPreset", attributes.get("rag_preset"));
        putIfPresent(values, "retrievalOptions", attributes.get("retrieval_options"));
        return values;
    }

    private void putIfPresent(Map<String, Object> values, String key, Object value) {
        if (value != null) {
            values.put(key, value);
        }
    }

    private EvaluationCostSnapshot extractCostSnapshot(RagRun run) {
        Map<String, Object> tokenUsage = new LinkedHashMap<>();
        Map<String, Object> latencyBreakdown = new LinkedHashMap<>();
        Map<String, Object> attributes = run.getTraceAttributes() == null ? Map.of() : run.getTraceAttributes();
        mergeMap(tokenUsage, attributes.get("token_usage"));
        mergeMap(tokenUsage, attributes.get("usage"));
        mergeMap(latencyBreakdown, attributes.get("latency_breakdown"));

        if (run.getTraceSteps() != null) {
            for (Map<String, Object> step : run.getTraceSteps()) {
                String name = stringValue(step.get("name"));
                Object payload = step.get("payload");
                if (name != null) {
                    Long latency = longValue(step.get("latency_ms"));
                    if (latency != null) {
                        latencyBreakdown.put(name, latency);
                    }
                }
                if (payload instanceof Map<?, ?> payloadMap) {
                    mergeMap(tokenUsage, payloadMap.get("token_usage"));
                    mergeMap(tokenUsage, payloadMap.get("usage"));
                    Long payloadLatency = longValue(payloadMap.get("latency_ms"));
                    if (name != null && payloadLatency != null) {
                        latencyBreakdown.put(name, payloadLatency);
                    }
                }
            }
        }

        Integer promptTokens = intValue(firstPresent(tokenUsage, "prompt_tokens", "promptTokens", "input_tokens", "inputTokens"));
        Integer completionTokens = intValue(firstPresent(tokenUsage, "completion_tokens", "completionTokens", "output_tokens", "outputTokens"));
        Integer totalTokens = intValue(firstPresent(tokenUsage, "total_tokens", "totalTokens"));
        if (totalTokens == null && (promptTokens != null || completionTokens != null)) {
            totalTokens = (promptTokens == null ? 0 : promptTokens) + (completionTokens == null ? 0 : completionTokens);
        }
        Integer embeddingTokens = intValue(firstPresent(tokenUsage, "embedding_tokens", "embeddingTokens"));
        Integer rerankTokens = intValue(firstPresent(tokenUsage, "rerank_tokens", "rerankTokens"));
        Double estimatedCost = doubleValue(firstPresent(tokenUsage, "estimated_cost", "estimatedCost", "cost"));

        return new EvaluationCostSnapshot(
                promptTokens,
                completionTokens,
                totalTokens,
                embeddingTokens,
                rerankTokens,
                estimatedCost,
                latencyFor(latencyBreakdown, "embed_query", "embed_retrieval_query", "embedding"),
                latencyFor(latencyBreakdown, "retrieve", "retrieval"),
                latencyFor(latencyBreakdown, "rerank"),
                latencyFor(latencyBreakdown, "generate", "generate_answer", "llm"),
                tokenUsage,
                latencyBreakdown
        );
    }

    @SuppressWarnings("unchecked")
    private void mergeMap(Map<String, Object> target, Object value) {
        if (value instanceof Map<?, ?> map) {
            map.forEach((key, item) -> {
                if (key != null && item != null) {
                    target.put(String.valueOf(key), item);
                }
            });
        }
    }

    private Object firstPresent(Map<String, Object> values, String... keys) {
        for (String key : keys) {
            if (values.containsKey(key)) {
                return values.get(key);
            }
        }
        return null;
    }

    private Long latencyFor(Map<String, Object> values, String... keys) {
        for (String key : keys) {
            Long value = longValue(values.get(key));
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private String stringValue(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private Integer intValue(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value instanceof String text && !text.isBlank()) {
            try {
                return Integer.parseInt(text);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private Long longValue(Object value) {
        if (value instanceof Number number) {
            return number.longValue();
        }
        if (value instanceof String text && !text.isBlank()) {
            try {
                return Math.round(Double.parseDouble(text));
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private Double doubleValue(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value instanceof String text && !text.isBlank()) {
            try {
                return Double.parseDouble(text);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private record EvaluationCostSnapshot(
            Integer promptTokens,
            Integer completionTokens,
            Integer totalTokens,
            Integer embeddingTokens,
            Integer rerankTokens,
            Double estimatedCost,
            Long embeddingLatencyMs,
            Long retrievalLatencyMs,
            Long rerankLatencyMs,
            Long llmLatencyMs,
            Map<String, Object> tokenUsage,
            Map<String, Object> latencyBreakdown
    ) {
    }
}
