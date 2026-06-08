package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagEvaluateRequest;
import com.example.agentknowledge.client.dto.AiRagEvaluateResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.RagExperiment;
import com.example.agentknowledge.domain.RagExperimentEvaluation;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.CreateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationHistoryResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationSummaryResponse;
import com.example.agentknowledge.dto.rag.RagExperimentResponse;
import com.example.agentknowledge.dto.rag.UpdateRagExperimentRequest;
import com.example.agentknowledge.repository.RagExperimentRepository;
import com.example.agentknowledge.repository.RagExperimentEvaluationRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RagExperimentService {

    private final RagExperimentRepository ragExperimentRepository;
    private final RagExperimentEvaluationRepository ragExperimentEvaluationRepository;
    private final RagRunRepository ragRunRepository;
    private final RagRetrievalResultRepository ragRetrievalResultRepository;
    private final KnowledgeBaseService knowledgeBaseService;
    private final AiServiceGateway aiServiceGateway;

    public RagExperimentService(
            RagExperimentRepository ragExperimentRepository,
            RagExperimentEvaluationRepository ragExperimentEvaluationRepository,
            RagRunRepository ragRunRepository,
            RagRetrievalResultRepository ragRetrievalResultRepository,
            KnowledgeBaseService knowledgeBaseService,
            AiServiceGateway aiServiceGateway
    ) {
        this.ragExperimentRepository = ragExperimentRepository;
        this.ragExperimentEvaluationRepository = ragExperimentEvaluationRepository;
        this.ragRunRepository = ragRunRepository;
        this.ragRetrievalResultRepository = ragRetrievalResultRepository;
        this.knowledgeBaseService = knowledgeBaseService;
        this.aiServiceGateway = aiServiceGateway;
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

        Double groundedScore = evaluation.result() == null ? null : evaluation.result().groundedScore();
        Double retrievalScore = evaluation.result() == null ? null : evaluation.result().retrievalScore();
        List<String> notes = evaluation.result() == null || evaluation.result().notes() == null
                ? List.of()
                : evaluation.result().notes();
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
                groundedScore,
                retrievalScore,
                notes
        );
        RagExperimentResponse updated = toResponse(savedExperiment);
        return new RagExperimentEvaluationResponse(
                updated,
                toEvaluationHistoryResponse(savedEvaluation),
                groundedScore,
                retrievalScore,
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

    private RagExperiment getEntity(UUID id) {
        return ragExperimentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("RAG experiment not found: " + id));
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
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

    private RagExperimentEvaluation saveEvaluationHistory(
            RagExperiment experiment,
            RagRun run,
            String expectedAnswer,
            Double groundedScore,
            Double retrievalScore,
            List<String> notes
    ) {
        RagExperimentEvaluation evaluation = new RagExperimentEvaluation();
        evaluation.setExperiment(experiment);
        evaluation.setRun(run);
        evaluation.setGroundedScore(groundedScore);
        evaluation.setRetrievalScore(retrievalScore);
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
}
