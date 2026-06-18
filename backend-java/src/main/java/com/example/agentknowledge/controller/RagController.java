package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.rag.BackfillRagasReportRequest;
import com.example.agentknowledge.dto.rag.CreateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.CreateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.EvaluateRagExperimentRequest;
import com.example.agentknowledge.dto.rag.ImportRagEvaluationCasesRequest;
import com.example.agentknowledge.dto.rag.ImportRagEvaluationCasesResponse;
import com.example.agentknowledge.dto.rag.RagEvaluationCaseResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationHistoryResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationResponse;
import com.example.agentknowledge.dto.rag.RagExperimentEvaluationSummaryResponse;
import com.example.agentknowledge.dto.rag.RagExperimentResponse;
import com.example.agentknowledge.dto.rag.RagQueryRequest;
import com.example.agentknowledge.dto.rag.RagQueryResponse;
import com.example.agentknowledge.dto.rag.RagRunResponse;
import com.example.agentknowledge.dto.rag.RagRunSummaryResponse;
import com.example.agentknowledge.dto.rag.RunEvaluationCasesBatchRequest;
import com.example.agentknowledge.dto.rag.RunEvaluationCasesBatchResponse;
import com.example.agentknowledge.dto.rag.UpdateRagEvaluationCaseRequest;
import com.example.agentknowledge.dto.rag.UpdateRagExperimentRequest;
import com.example.agentknowledge.service.RagExperimentService;
import com.example.agentknowledge.service.RagService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/rag")
public class RagController {

    private final RagService ragService;
    private final RagExperimentService ragExperimentService;

    public RagController(RagService ragService, RagExperimentService ragExperimentService) {
        this.ragService = ragService;
        this.ragExperimentService = ragExperimentService;
    }

    @PostMapping("/query")
    public ApiResponse<RagQueryResponse> query(@Valid @RequestBody RagQueryRequest request) {
        return ApiResponse.success(ragService.query(request), TraceContext.getTraceId());
    }

    @GetMapping("/runs")
    public ApiResponse<List<RagRunSummaryResponse>> listRuns(
            @RequestParam(name = "limit", required = false) Integer limit
    ) {
        return ApiResponse.success(ragService.listRecentRuns(limit), TraceContext.getTraceId());
    }

    @GetMapping("/runs/{id}")
    public ApiResponse<RagRunResponse> getRun(@PathVariable UUID id) {
        return ApiResponse.success(ragService.getRun(id), TraceContext.getTraceId());
    }

    @GetMapping("/experiments")
    public ApiResponse<List<RagExperimentResponse>> listExperiments() {
        return ApiResponse.success(ragExperimentService.list(), TraceContext.getTraceId());
    }

    @GetMapping("/experiment-evaluations/summary")
    public ApiResponse<RagExperimentEvaluationSummaryResponse> summarizeExperimentEvaluations(
            @RequestParam(name = "limit", required = false) Integer limit
    ) {
        return ApiResponse.success(ragExperimentService.summarizeEvaluations(limit), TraceContext.getTraceId());
    }

    @PutMapping("/experiment-evaluations/ragas-report")
    public ApiResponse<RagExperimentEvaluationHistoryResponse> backfillRagasReport(
            @Valid @RequestBody BackfillRagasReportRequest request
    ) {
        return ApiResponse.success(ragExperimentService.backfillRagasReport(request), TraceContext.getTraceId());
    }

    @GetMapping("/evaluation-cases")
    public ApiResponse<List<RagEvaluationCaseResponse>> listEvaluationCases(
            @RequestParam(name = "experimentId", required = false) UUID experimentId
    ) {
        return ApiResponse.success(ragExperimentService.listEvaluationCases(experimentId), TraceContext.getTraceId());
    }

    @PostMapping("/evaluation-cases")
    public ApiResponse<RagEvaluationCaseResponse> createEvaluationCase(
            @Valid @RequestBody CreateRagEvaluationCaseRequest request
    ) {
        return ApiResponse.success(ragExperimentService.createEvaluationCase(request), TraceContext.getTraceId());
    }

    @PostMapping("/evaluation-cases/import")
    public ApiResponse<ImportRagEvaluationCasesResponse> importEvaluationCases(
            @Valid @RequestBody ImportRagEvaluationCasesRequest request
    ) {
        return ApiResponse.success(ragExperimentService.importEvaluationCases(request), TraceContext.getTraceId());
    }

    @PutMapping("/evaluation-cases/{id}")
    public ApiResponse<RagEvaluationCaseResponse> updateEvaluationCase(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateRagEvaluationCaseRequest request
    ) {
        return ApiResponse.success(ragExperimentService.updateEvaluationCase(id, request), TraceContext.getTraceId());
    }

    @DeleteMapping("/evaluation-cases/{id}")
    public ApiResponse<Void> deleteEvaluationCase(@PathVariable UUID id) {
        ragExperimentService.deleteEvaluationCase(id);
        return ApiResponse.success(null, TraceContext.getTraceId());
    }

    @PostMapping("/evaluation-cases/{id}/evaluate")
    public ApiResponse<RagExperimentEvaluationResponse> evaluateEvaluationCase(
            @PathVariable UUID id,
            @Valid @RequestBody EvaluateRagEvaluationCaseRequest request
    ) {
        return ApiResponse.success(ragExperimentService.evaluateCase(id, request), TraceContext.getTraceId());
    }

    @PostMapping("/evaluation-cases/run-batch")
    public ApiResponse<RunEvaluationCasesBatchResponse> runEvaluationCasesBatch(
            @Valid @RequestBody RunEvaluationCasesBatchRequest request
    ) {
        return ApiResponse.success(ragExperimentService.runBatch(request), TraceContext.getTraceId());
    }

    @GetMapping("/experiments/{id}")
    public ApiResponse<RagExperimentResponse> getExperiment(@PathVariable UUID id) {
        return ApiResponse.success(ragExperimentService.get(id), TraceContext.getTraceId());
    }

    @PostMapping("/experiments")
    public ApiResponse<RagExperimentResponse> createExperiment(@Valid @RequestBody CreateRagExperimentRequest request) {
        return ApiResponse.success(ragExperimentService.create(request), TraceContext.getTraceId());
    }

    @PutMapping("/experiments/{id}")
    public ApiResponse<RagExperimentResponse> updateExperiment(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateRagExperimentRequest request
    ) {
        return ApiResponse.success(ragExperimentService.update(id, request), TraceContext.getTraceId());
    }

    @PostMapping("/experiments/{id}/evaluate")
    public ApiResponse<RagExperimentEvaluationResponse> evaluateExperiment(
            @PathVariable UUID id,
            @Valid @RequestBody EvaluateRagExperimentRequest request
    ) {
        return ApiResponse.success(ragExperimentService.evaluate(id, request), TraceContext.getTraceId());
    }

    @DeleteMapping("/experiments/{id}")
    public ApiResponse<Void> deleteExperiment(@PathVariable UUID id) {
        ragExperimentService.delete(id);
        return ApiResponse.success(null, TraceContext.getTraceId());
    }
}
