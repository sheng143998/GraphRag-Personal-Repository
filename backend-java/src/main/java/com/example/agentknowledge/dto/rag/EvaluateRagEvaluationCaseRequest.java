package com.example.agentknowledge.dto.rag;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record EvaluateRagEvaluationCaseRequest(
        @NotNull UUID runId,
        String expectedAnswer
) {
}
