package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiRagEvaluateRequest;
import com.example.agentknowledge.client.dto.AiRagEvaluateResponse;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.RagEvaluationCase;
import com.example.agentknowledge.domain.RagExperiment;
import com.example.agentknowledge.domain.RagExperimentEvaluation;
import com.example.agentknowledge.domain.RagRetrievalResult;
import com.example.agentknowledge.domain.RagRun;
import com.example.agentknowledge.dto.rag.BackfillRagasReportRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationResponse;
import com.example.agentknowledge.repository.RagEvaluationCaseRepository;
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
    private final RagEvaluationCaseRepository evaluationCaseRepository = mock(RagEvaluationCaseRepository.class);
    private final RagExperimentEvaluationRepository evaluationRepository = mock(RagExperimentEvaluationRepository.class);
    private final RagRunRepository ragRunRepository = mock(RagRunRepository.class);
    private final RagRetrievalResultRepository retrievalResultRepository = mock(RagRetrievalResultRepository.class);
    private final KnowledgeBaseService knowledgeBaseService = mock(KnowledgeBaseService.class);
    private final AiServiceGateway aiServiceGateway = mock(AiServiceGateway.class);
    private final RagService ragService = mock(RagService.class);

    private final RagExperimentService service = new RagExperimentService(
            experimentRepository,
            evaluationCaseRepository,
            evaluationRepository,
            ragRunRepository,
            retrievalResultRepository,
            knowledgeBaseService,
            aiServiceGateway,
            ragService
    );

    @Test
    void evaluateStoresAiScoresOnExperiment() {
        UUID experimentId = UUID.randomUUID();
        UUID runId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        UUID relevantChunkId = UUID.randomUUID();
        UUID relevantDocumentId = UUID.randomUUID();
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
        run.setPromptName("rag_answer");
        run.setPromptVersion("v1");
        run.setLatencyMs(42L);
        run.setTraceAttributes(Map.of(
                "token_usage", Map.of(
                        "prompt_tokens", 120,
                        "completion_tokens", 30,
                        "total_tokens", 150,
                        "estimated_cost", 0.012
                ),
                "rag_preset", Map.of("query_rewrite", true),
                "retrieval_options", Map.of("vectorWeight", 0.7, "keywordWeight", 0.3)
        ));
        run.setTraceSteps(List.of(
                Map.of("name", "embed_query", "payload", Map.of("latency_ms", 11)),
                Map.of("name", "retrieve", "payload", Map.of("latency_ms", 22)),
                Map.of("name", "rerank", "payload", Map.of("latency_ms", 33)),
                Map.of("name", "generate", "payload", Map.of("latency_ms", 44))
        ));
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
                                1.0,
                                0.5,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                1.0,
                                null,
                                null,
                                null,
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
                new EvaluateRagExperimentRequest(
                        runId,
                        "Expected answer",
                        "advanced-rag-rerank",
                        List.of(relevantChunkId),
                        List.of(),
                        List.of(),
                        List.of(relevantChunkId),
                        List.of(relevantChunkId),
                        List.of(relevantDocumentId),
                        List.of(relevantChunkId),
                        3
                )
        );

        assertThat(response.groundedScore()).isEqualTo(0.91);
        assertThat(response.retrievalScore()).isEqualTo(0.82);
        assertThat(response.recallAtK()).isEqualTo(1.0);
        assertThat(response.precisionAtK()).isEqualTo(0.5);
        assertThat(response.chunkRecallAtK()).isEqualTo(1.0);
        assertThat(response.documentRecallAtK()).isEqualTo(1.0);
        assertThat(response.evidenceRecallAtK()).isEqualTo(1.0);
        assertThat(response.mrr()).isEqualTo(1.0);
        assertThat(response.citationHit()).isEqualTo(1.0);
        assertThat(response.experiment().status()).isEqualTo("COMPLETED");
        assertThat(response.experiment().precisionScore()).isEqualTo(0.91);
        assertThat(response.experiment().recallScore()).isEqualTo(0.82);
        assertThat(response.experiment().notes()).contains("Evaluation run " + runId);
        assertThat(response.evaluation().runId()).isEqualTo(runId);
        assertThat(response.evaluation().experimentName()).isEqualTo("Advanced RAG eval");
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
        assertThat(aiRequest.getValue().expectedAnswer()).isEqualTo("Expected answer");
        assertThat(aiRequest.getValue().citations()).hasSize(1);
        assertThat(aiRequest.getValue().context().knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(aiRequest.getValue().evaluationCase()).isNotNull();
        assertThat(aiRequest.getValue().evaluationCase().caseId()).isEqualTo("advanced-rag-rerank");
        assertThat(aiRequest.getValue().evaluationCase().requiredChunkIds()).containsExactly(relevantChunkId);
        assertThat(aiRequest.getValue().evaluationCase().citationChunkIds()).containsExactly(relevantChunkId);
        assertThat(aiRequest.getValue().evaluationCase().relevantChunkIds()).containsExactly(relevantChunkId);
        assertThat(aiRequest.getValue().evaluationCase().relevantDocumentIds()).containsExactly(relevantDocumentId);
        assertThat(aiRequest.getValue().evaluationCase().expectedCitationChunkIds()).containsExactly(relevantChunkId);
        assertThat(aiRequest.getValue().evaluationCase().topK()).isEqualTo(3);

        ArgumentCaptor<RagExperimentEvaluation> historyRecord = ArgumentCaptor.forClass(RagExperimentEvaluation.class);
        verify(evaluationRepository).save(historyRecord.capture());
        assertThat(historyRecord.getValue().getExperiment().getId()).isEqualTo(experimentId);
        assertThat(historyRecord.getValue().getRun().getId()).isEqualTo(runId);
        assertThat(historyRecord.getValue().getGroundedScore()).isEqualTo(0.91);
        assertThat(historyRecord.getValue().getRetrievalScore()).isEqualTo(0.82);
        assertThat(historyRecord.getValue().getRecallAtK()).isEqualTo(1.0);
        assertThat(historyRecord.getValue().getPrecisionAtK()).isEqualTo(0.5);
        assertThat(historyRecord.getValue().getChunkRecallAtK()).isEqualTo(1.0);
        assertThat(historyRecord.getValue().getDocumentRecallAtK()).isEqualTo(1.0);
        assertThat(historyRecord.getValue().getEvidenceRecallAtK()).isEqualTo(1.0);
        assertThat(historyRecord.getValue().getMrr()).isEqualTo(1.0);
        assertThat(historyRecord.getValue().getCitationHit()).isEqualTo(1.0);
        assertThat(historyRecord.getValue().getPromptTokens()).isEqualTo(120);
        assertThat(historyRecord.getValue().getCompletionTokens()).isEqualTo(30);
        assertThat(historyRecord.getValue().getTotalTokens()).isEqualTo(150);
        assertThat(historyRecord.getValue().getEstimatedCost()).isEqualTo(0.012);
        assertThat(historyRecord.getValue().getEmbeddingLatencyMs()).isEqualTo(11L);
        assertThat(historyRecord.getValue().getRetrievalLatencyMs()).isEqualTo(22L);
        assertThat(historyRecord.getValue().getRerankLatencyMs()).isEqualTo(33L);
        assertThat(historyRecord.getValue().getLlmLatencyMs()).isEqualTo(44L);
        assertThat(historyRecord.getValue().getStrategyConfig()).containsEntry("strategyName", "advanced-rag");
        assertThat(historyRecord.getValue().getNotes()).contains("Grounded answer");
    }

    @Test
    void evaluateCaseUsesPersistedLabelsAndExpectedAnswerOverride() {
        UUID caseId = UUID.randomUUID();
        UUID experimentId = UUID.randomUUID();
        UUID runId = UUID.randomUUID();
        UUID relevantChunkId = UUID.randomUUID();
        UUID citationChunkId = UUID.randomUUID();
        UUID relevantDocumentId = UUID.randomUUID();
        RagExperiment experiment = new RagExperiment();
        experiment.setId(experimentId);
        experiment.setName("Dataset eval");
        experiment.setStrategyName("advanced-rag");
        RagEvaluationCase evaluationCase = new RagEvaluationCase();
        evaluationCase.setId(caseId);
        evaluationCase.setExperiment(experiment);
        evaluationCase.setCaseId("case-001");
        evaluationCase.setQuestion("How does rerank help retrieval?");
        evaluationCase.setExpectedAnswer("Persisted answer");
        evaluationCase.setRequiredChunkIds(List.of(relevantChunkId));
        evaluationCase.setCitationChunkIds(List.of(citationChunkId));
        evaluationCase.setRelevantChunkIds(List.of(relevantChunkId));
        evaluationCase.setRelevantDocumentIds(List.of(relevantDocumentId));
        evaluationCase.setExpectedCitationChunkIds(List.of(citationChunkId));
        evaluationCase.setEvaluationTopK(7);
        RagRun run = new RagRun();
        run.setId(runId);
        run.setQuestion("How does rerank help retrieval?");
        run.setAnswer("Generated answer");
        run.setStrategyName("advanced-rag");
        run.setRetrieverType("hybrid");
        run.setModelName("stub-llm");
        run.setLatencyMs(31L);
        run.setCreatedAt(Instant.parse("2026-06-08T16:44:00Z"));

        when(evaluationCaseRepository.findById(caseId)).thenReturn(Optional.of(evaluationCase));
        when(experimentRepository.findById(experimentId)).thenReturn(Optional.of(experiment));
        when(ragRunRepository.findById(runId)).thenReturn(Optional.of(run));
        when(retrievalResultRepository.findByRunIdOrderByRankAsc(runId)).thenReturn(List.of());
        when(aiServiceGateway.evaluateRag(any(AiRagEvaluateRequest.class), any())).thenReturn(
                new AiRagEvaluateResponse(
                        new AiRagEvaluateResponse.Result(
                                0.8,
                                0.7,
                                null,
                                null,
                                null,
                                null,
                                null,
                                null,
                                null,
                                null,
                                null,
                                null,
                                List.of("case evaluated")
                        ),
                        null
                )
        );
        when(experimentRepository.save(experiment)).thenReturn(experiment);
        when(evaluationRepository.save(any(RagExperimentEvaluation.class))).thenAnswer(invocation -> {
            RagExperimentEvaluation saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            saved.setCreatedAt(Instant.parse("2026-06-08T16:45:00Z"));
            return saved;
        });
        when(evaluationRepository.findByExperiment_IdOrderByCreatedAtDesc(any(UUID.class), any(PageRequest.class)))
                .thenReturn(List.of());

        service.evaluateCase(
                caseId,
                new EvaluateRagEvaluationCaseRequest(runId, "Override answer")
        );

        ArgumentCaptor<AiRagEvaluateRequest> aiRequest = ArgumentCaptor.forClass(AiRagEvaluateRequest.class);
        verify(aiServiceGateway).evaluateRag(aiRequest.capture(), any());
        assertThat(aiRequest.getValue().expectedAnswer()).isEqualTo("Override answer");
        assertThat(aiRequest.getValue().evaluationCase().caseId()).isEqualTo("case-001");
        assertThat(aiRequest.getValue().evaluationCase().requiredChunkIds()).containsExactly(relevantChunkId);
        assertThat(aiRequest.getValue().evaluationCase().citationChunkIds()).containsExactly(citationChunkId);
        assertThat(aiRequest.getValue().evaluationCase().relevantChunkIds()).containsExactly(relevantChunkId);
        assertThat(aiRequest.getValue().evaluationCase().relevantDocumentIds()).containsExactly(relevantDocumentId);
        assertThat(aiRequest.getValue().evaluationCase().expectedCitationChunkIds()).containsExactly(citationChunkId);
        assertThat(aiRequest.getValue().evaluationCase().topK()).isEqualTo(7);
    }

    @Test
    void backfillRagasReportByEvaluationIdStoresReportAndReturnsFields() {
        UUID evaluationId = UUID.randomUUID();
        RagExperiment experiment = experiment("Offline RAGAS eval");
        RagRun run = run("How did RAGAS score this answer?", "advanced-rag", 55L);
        RagExperimentEvaluation evaluation = evaluation(experiment, run, 0.8, 0.7);
        evaluation.setId(evaluationId);

        when(evaluationRepository.findById(evaluationId)).thenReturn(Optional.of(evaluation));
        when(evaluationRepository.save(any(RagExperimentEvaluation.class))).thenAnswer(invocation -> invocation.getArgument(0));

        var response = service.backfillRagasReport(new BackfillRagasReportRequest(
                evaluationId,
                null,
                null,
                null,
                Map.of("faithfulness", 0.88, "answer_relevancy", 0.77),
                List.of("faithfulness", "answer_relevancy"),
                "0.2.15",
                "gpt-4o-mini",
                "file:///reports/ragas-evaluation.json"
        ));

        assertThat(response.id()).isEqualTo(evaluationId);
        assertThat(response.ragasScores()).containsEntry("faithfulness", 0.88);
        assertThat(response.ragasScores()).containsEntry("answer_relevancy", 0.77);
        assertThat(response.ragasMetricNames()).containsExactly("faithfulness", "answer_relevancy");
        assertThat(response.ragasVersion()).isEqualTo("0.2.15");
        assertThat(response.ragasJudgeModel()).isEqualTo("gpt-4o-mini");
        assertThat(response.ragasReportUri()).isEqualTo("file:///reports/ragas-evaluation.json");

        ArgumentCaptor<RagExperimentEvaluation> savedEvaluation = ArgumentCaptor.forClass(RagExperimentEvaluation.class);
        verify(evaluationRepository).save(savedEvaluation.capture());
        assertThat(savedEvaluation.getValue().getRagasScores()).containsEntry("faithfulness", 0.88);
        assertThat(savedEvaluation.getValue().getRagasMetricNames()).containsExactly("faithfulness", "answer_relevancy");
        assertThat(savedEvaluation.getValue().getRagasVersion()).isEqualTo("0.2.15");
        assertThat(savedEvaluation.getValue().getRagasJudgeModel()).isEqualTo("gpt-4o-mini");
        assertThat(savedEvaluation.getValue().getRagasReportUri()).isEqualTo("file:///reports/ragas-evaluation.json");
    }

    @Test
    void backfillRagasReportCanLocateEvaluationByExperimentAndRun() {
        UUID caseId = UUID.randomUUID();
        RagExperiment experiment = experiment("Case-linked RAGAS eval");
        RagRun run = run("How does a persisted case map to a run?", "advanced-rag", 61L);
        RagEvaluationCase evaluationCase = new RagEvaluationCase();
        evaluationCase.setId(caseId);
        evaluationCase.setExperiment(experiment);
        evaluationCase.setCaseId("case-ragas-001");
        RagExperimentEvaluation evaluation = evaluation(experiment, run, 0.81, 0.71);

        when(evaluationCaseRepository.findById(caseId)).thenReturn(Optional.of(evaluationCase));
        when(evaluationRepository.findFirstByExperiment_IdAndRun_IdOrderByCreatedAtDesc(experiment.getId(), run.getId()))
                .thenReturn(Optional.of(evaluation));
        when(evaluationRepository.save(any(RagExperimentEvaluation.class))).thenAnswer(invocation -> invocation.getArgument(0));

        var response = service.backfillRagasReport(new BackfillRagasReportRequest(
                null,
                experiment.getId(),
                run.getId(),
                caseId,
                Map.of("context_precision", 0.92),
                List.of("context_precision"),
                "0.2.15",
                "gpt-4.1-mini",
                "s3://ragas/reports/case-ragas-001.json"
        ));

        assertThat(response.id()).isEqualTo(evaluation.getId());
        assertThat(response.ragasScores()).containsEntry("context_precision", 0.92);
        assertThat(response.ragasMetricNames()).containsExactly("context_precision");
        assertThat(response.ragasJudgeModel()).isEqualTo("gpt-4.1-mini");
    }

    @Test
    void summarizeEvaluationsReturnsRecentAggregateAndBestExperiment() {
        RagExperiment advancedExperiment = experiment("Advanced RAG eval");
        RagExperiment basicExperiment = experiment("Basic RAG eval");
        RagExperimentEvaluation advancedEvaluation = evaluation(
                advancedExperiment,
                run("How does advanced RAG rerank?", "advanced-rag", 80L),
                0.92,
                0.82
        );
        advancedEvaluation.setRagasScores(Map.of("faithfulness", 0.96));
        advancedEvaluation.setRagasMetricNames(List.of("faithfulness"));
        advancedEvaluation.setRagasVersion("0.2.15");
        advancedEvaluation.setRagasJudgeModel("gpt-4o-mini");
        advancedEvaluation.setRagasReportUri("file:///reports/advanced.json");
        RagExperimentEvaluation basicEvaluation = evaluation(
                basicExperiment,
                run("What is machine learning?", "basic-rag", 40L),
                0.72,
                0.62
        );
        when(evaluationRepository.findAllByOrderByCreatedAtDesc(any(PageRequest.class)))
                .thenReturn(List.of(advancedEvaluation, basicEvaluation));

        var summary = service.summarizeEvaluations(20);

        assertThat(summary.evaluationCount()).isEqualTo(2);
        assertThat(summary.averageGrounded()).isCloseTo(0.82, within(0.0001));
        assertThat(summary.averageRetrieval()).isCloseTo(0.72, within(0.0001));
        assertThat(summary.bestExperimentId()).isEqualTo(advancedExperiment.getId());
        assertThat(summary.bestExperimentName()).isEqualTo("Advanced RAG eval");
        assertThat(summary.recentEvaluations()).hasSize(2);
        assertThat(summary.recentEvaluations().get(0).runQuestion()).isEqualTo("How does advanced RAG rerank?");
        assertThat(summary.recentEvaluations().get(0).runStrategyName()).isEqualTo("advanced-rag");
        assertThat(summary.recentEvaluations().get(0).ragasScores()).containsEntry("faithfulness", 0.96);
        assertThat(summary.recentEvaluations().get(0).ragasMetricNames()).containsExactly("faithfulness");
        assertThat(summary.recentEvaluations().get(0).ragasVersion()).isEqualTo("0.2.15");
        assertThat(summary.recentEvaluations().get(0).ragasJudgeModel()).isEqualTo("gpt-4o-mini");
        assertThat(summary.recentEvaluations().get(0).ragasReportUri()).isEqualTo("file:///reports/advanced.json");
    }

    private RagExperiment experiment(String name) {
        RagExperiment experiment = new RagExperiment();
        experiment.setId(UUID.randomUUID());
        experiment.setName(name);
        return experiment;
    }

    private RagRun run(String question, String strategyName, Long latencyMs) {
        RagRun run = new RagRun();
        run.setId(UUID.randomUUID());
        run.setQuestion(question);
        run.setAnswer("Generated answer");
        run.setStrategyName(strategyName);
        run.setRetrieverType("hybrid");
        run.setModelName("stub-llm");
        run.setLatencyMs(latencyMs);
        run.setCreatedAt(Instant.parse("2026-06-08T16:50:00Z"));
        return run;
    }

    private RagExperimentEvaluation evaluation(
            RagExperiment experiment,
            RagRun run,
            Double groundedScore,
            Double retrievalScore
    ) {
        RagExperimentEvaluation evaluation = new RagExperimentEvaluation();
        evaluation.setId(UUID.randomUUID());
        evaluation.setExperiment(experiment);
        evaluation.setRun(run);
        evaluation.setGroundedScore(groundedScore);
        evaluation.setRetrievalScore(retrievalScore);
        evaluation.setGeneratedAnswer(run.getAnswer());
        evaluation.setCreatedAt(Instant.parse("2026-06-08T16:55:00Z"));
        return evaluation;
    }
}
