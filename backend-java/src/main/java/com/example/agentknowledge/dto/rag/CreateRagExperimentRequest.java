package com.example.agentknowledge.dto.rag;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import java.util.UUID;

public record CreateRagExperimentRequest(
        UUID knowledgeBaseId,
        @NotBlank @Size(max = 200) String name,
        @Size(max = 5000) String description,
        @NotBlank @Size(max = 100) String strategy,
        @Size(max = 200) String datasetName,
        @PositiveOrZero Integer sampleCount,
        @DecimalMin("0.0") @DecimalMax("1.0") Double precisionScore,
        @DecimalMin("0.0") @DecimalMax("1.0") Double recallScore,
        @Size(max = 32) String status,
        @Size(max = 5000) String notes
) {
}
