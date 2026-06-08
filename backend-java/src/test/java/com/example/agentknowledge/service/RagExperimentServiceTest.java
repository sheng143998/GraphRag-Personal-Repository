package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagEvaluateRequest;
import com.example.agentknowledge.client.dto.AiRagEvaluateResponse;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.RagExperiment;
import com.example.agentknowledge.domain.RagExperimentEvaluation;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.EvaluateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationResponse;
import com.example.agentknowledge.repository.RagExperimentEvaluationRepository;
import com.example.agentknowledge.repository.RagExperimentRepository;
import com.example.agentknowledge.repository.RagRetrievalResultRepository;
import com.example.agentknowledge.repository.RagRunRepository;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.data.domain.PageRequest;

class RagExperimentServiceTest {

    private final RagExperimentRepository experimentRepository = mock(RagExperimentRepository.class);
    private final RagExperimentEvaluationRepository evaluationRepository = mock(RagExperimentEvaluationRepository.class);
    private final RagRunRepository ragRunRepository = mock(RagRunRepository.class);
    private final RagRetrievalResultRepository retrievalResultRepository = mock(RagRetrievalResultRepository.class);
    private final KnowledgeBaseService knowledgeBaseService = mock(KnowledgeBaseService.class);
    private final AiServiceGateway aiServiceGateway = mock(AiServiceGateway.class);

    private final RagExperimentService service = new RagExperimentService(
            experimentRepository,
            evaluationRepository,
            ragRunRepository,
            retrievalResultRepository,
            knowledgeBaseService,
            aiServiceGateway
    );

    @Test
    void evaluateStoresAiScoresOnExperiment() {
        UUID experimentId = UUID.randomUUID();
        UUID runId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        RagExperiment experiment = new RagExperiment();
        experiment.setId(experimentId);
        experiment.setName("Advanced RAG eval");
        experiment.setStrategyName("advanced-rag");
        experiment.setStatus("PLANNED");
        RagRun run = new RagRun();
        run.setId(runId);
        run.setKnowledgeBase(knowledgeBase);
        run.setQuestion("How does advanced RAG prove rerank works?");
        run.setAnswer("Use run traces and retrieval metrics.");
        run.setStrategyName("advanced-rag");
        run.setRetrieverType("hybrid");
        run.setModelName("stub-llm");
        run.setLatencyMs(42L);
        run.setCreatedAt(Instant.parse("2026-06-08T16:44:00Z"));
        RagRetrievalResult retrievalResult = new RagRetrievalResult();
        retrievalResult.setRun(run);
        retrievalResult.setRank(1);
        retrievalResult.setScore(0.7);
        retrievalResult.setRerankScore(0.9);
        retrievalResult.setSource("advanced-rag-notes.md");
        retrievalResult.setMetadata(Map.of("content_preview", "Rerank evidence"));

        when(experimentRepository.findById(experimentId)).thenReturn(Optional.of(experiment));
        when(ragRunRepository.findById(runId)).thenReturn(Optional.of(run));
        when(retrievalResultRepository.findByRunIdOrderByRankAsc(runId)).thenReturn(List.of(retrievalResult));
        when(aiServiceGateway.evaluateRag(any(AiRagEvaluateRequest.class), any())).thenReturn(
                new AiRagEvaluateResponse(
                        new AiRagEvaluateResponse.Result(
                                0.91,
                                0.82,
                                List.of("Grounded answer with one relevant citation.")
                        ),
                        null
                )
        );
        when(experimentRepository.save(experiment)).thenReturn(experiment);
        AtomicReference<RagExperimentEvaluation> savedEvaluationRef = new AtomicReference<>();
        when(evaluationRepository.save(any(RagExperimentEvaluation.class))).thenAnswer(invocation -> {
            RagExperimentEvaluation saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            saved.setCreatedAt(Instant.parse("2026-06-08T16:45:00Z"));
            savedEvaluationRef.set(saved);
            return saved;
        });
        when(evaluationRepository.findByExperiment_IdOrderByCreatedAtDesc(
                any(UUID.class),
                any(PageRequest.class)
        )).thenAnswer(invocation -> savedEvaluationRef.get() == null ? List.of() : List.of(savedEvaluationRef.get()));

        RagExperimentEvaluationResponse response = service.evaluate(
                experimentId,
                new EvaluateRagExperimentRequest(runId, "Expected answer")
        );

        assertThat(response.groundedScore()).isEqualTo(0.91);
        assertThat(response.retrievalScore()).isEqualTo(0.82);
        assertThat(response.experiment().status()).isEqualTo("COMPLETED");
        assertThat(response.experiment().precisionScore()).isEqualTo(0.91);
        assertThat(response.experiment().recallScore()).isEqualTo(0.82);
        assertThat(response.experiment().notes()).contains("Evaluation run " + runId);
        assertThat(response.evaluation().runId()).isEqualTo(runId);
        assertThat(response.evaluation().runQuestion()).isEqualTo(run.getQuestion());
        assertThat(response.evaluation().runStrategyName()).isEqualTo("advanced-rag");
        assertThat(response.evaluation().runRetrieverType()).isEqualTo("hybrid");
        assertThat(response.evaluation().runModelName()).isEqualTo("stub-llm");
        assertThat(response.evaluation().runLatencyMs()).isEqualTo(42L);
        assertThat(response.evaluation().runCreatedAt()).isEqualTo(run.getCreatedAt());
        assertThat(response.evaluation().expectedAnswer()).isEqualTo("Expected answer");
        assertThat(response.evaluation().generatedAnswer()).isEqualTo(run.getAnswer());
        assertThat(response.history()).hasSize(1);
        assertThat(response.experiment().evaluations()).hasSize(1);

        ArgumentCaptor<AiRagEvaluateRequest> aiRequest = ArgumentCaptor.forClass(AiRagEvaluateRequest.class);
        verify(aiServiceGateway).evaluateRag(aiRequest.capture(), any());
        assertThat(aiRequest.getValue().question()).isEqualTo(run.getQuestion());
        assertThat(aiRequest.getValue().generatedAnswer()).isEqualTo(run.getAnswer());
        assertThat(aiRequest.getValue().citations()).hasSize(1);
        assertThat(aiRequest.getValue().context().knowledgeBaseId()).isEqualTo(knowledgeBaseId);

        ArgumentCaptor<RagExperimentEvaluation> historyRecord = ArgumentCaptor.forClass(RagExperimentEvaluation.class);
        verify(evaluationRepository).save(historyRecord.capture());
        assertThat(historyRecord.getValue().getExperiment().getId()).isEqualTo(experimentId);
        assertThat(historyRecord.getValue().getRun().getId()).isEqualTo(runId);
        assertThat(historyRecord.getValue().getGroundedScore()).isEqualTo(0.91);
        assertThat(historyRecord.getValue().getRetrievalScore()).isEqualTo(0.82);
        assertThat(historyRecord.getValue().getNotes()).contains("Grounded answer");
    }
}
