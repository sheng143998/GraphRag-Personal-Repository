package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagEvaluateRequest;
import com.example.agentknowledge.client.dto.AiRagEvaluateResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.RagExperiment;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.CreateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationResponse;
import com.example.agentknowledge.dto.rag.RagExperimentResponse;
import com.example.agentknowledge.dto.rag.UpdateRagExperimentRequest;
import com.example.agentknowledge.repository.RagExperimentRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class RagExperimentService {

    private final RagExperimentRepository ragExperimentRepository;
    private final RagRunRepository ragRunRepository;
    private final RagRetrievalResultRepository ragRetrievalResultRepository;
    private final KnowledgeBaseService knowledgeBaseService;
    private final AiServiceGateway aiServiceGateway;

    public RagExperimentService(
            RagExperimentRepository ragExperimentRepository,
            RagRunRepository ragRunRepository,
            RagRetrievalResultRepository ragRetrievalResultRepository,
            KnowledgeBaseService knowledgeBaseService,
            AiServiceGateway aiServiceGateway
    ) {
        this.ragExperimentRepository = ragExperimentRepository;
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
                        )
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
        RagExperimentResponse updated = toResponse(ragExperimentRepository.save(experiment));
        return new RagExperimentEvaluationResponse(updated, groundedScore, retrievalScore, notes);
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
                experiment.getUpdatedAt()
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

    private String formatEvaluationNotes(String existingNotes, UUID runId, List<String> notes) {
        String evaluationLine = "Evaluation run " + runId + ": " + String.join(" ", notes);
        if (existingNotes == null || existingNotes.isBlank()) {
            return evaluationLine;
        }
        return existingNotes + "\n" + evaluationLine;
    }
}
