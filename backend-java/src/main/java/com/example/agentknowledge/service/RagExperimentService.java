package com.example.agentknowledge.service;

import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.RagExperiment;
import com.example.agentknowledge.dto.rag.CreateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.RagExperimentResponse;
import com.example.agentknowledge.dto.rag.UpdateRagExperimentRequest;
import com.example.agentknowledge.repository.RagExperimentRepository;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class RagExperimentService {

    private final RagExperimentRepository ragExperimentRepository;
    private final KnowledgeBaseService knowledgeBaseService;

    public RagExperimentService(
            RagExperimentRepository ragExperimentRepository,
            KnowledgeBaseService knowledgeBaseService
    ) {
        this.ragExperimentRepository = ragExperimentRepository;
        this.knowledgeBaseService = knowledgeBaseService;
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
        return value == null ? "待评估" : String.format(Locale.ROOT, "%.2f", value);
    }
}
