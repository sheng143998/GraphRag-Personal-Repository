package com.example.agentknowledge.dto.chat;

public record LearningWeakPointSummaryResponse(
        int totalCount,
        int needsReviewCount,
        int masteredCount,
        int hardCount,
        int totalReviewCount,
        double completionRate,
        LearningWeakPointResponse nextWeakPoint
) {
}
