package com.example.agentknowledge.dto.rag;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.UUID;

public record EvaluateRagExperimentRequest(
        @NotNull UUID runId,
        @Size(max = 5000) String expectedAnswer
) {
}
