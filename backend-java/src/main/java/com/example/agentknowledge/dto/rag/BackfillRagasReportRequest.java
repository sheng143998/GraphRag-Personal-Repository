package com.example.agentknowledge.dto.rag;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.validation.constraints.AssertTrue;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record BackfillRagasReportRequest(
        UUID evaluationId,
        UUID experimentId,
        UUID runId,
        UUID evaluationCaseId,
        Map<String, Object> ragasScores,
        List<String> ragasMetricNames,
        String ragasVersion,
        String ragasJudgeModel,
        String ragasReportUri
) {

    @JsonIgnore
    @AssertTrue(message = "provide evaluationId, or runId with experimentId")
    public boolean isLocatorPresent() {
        return evaluationId != null || (runId != null && experimentId != null);
    }
}
