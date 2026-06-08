package com.example.agentknowledge.dto.chat;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record CreateWeakPointPracticeTurnRequest(
        String strategyName,
        @Min(1) @Max(20) Integer topK,
        String userAnswer,
        Boolean autoAssess
) {
}
