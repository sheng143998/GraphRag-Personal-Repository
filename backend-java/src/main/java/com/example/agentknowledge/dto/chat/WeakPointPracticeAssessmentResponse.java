package com.example.agentknowledge.dto.chat;

public record WeakPointPracticeAssessmentResponse(
        double score,
        boolean passed,
        String masteryStatus,
        String difficulty,
        String feedback
) {
}
