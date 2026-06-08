package com.example.agentknowledge.dto.chat;

public record WeakPointPracticeTurnResponse(
        LearningWeakPointResponse weakPoint,
        LearningWeakPointResponse updatedWeakPoint,
        WeakPointPracticeAssessmentResponse assessment,
        LearningWeakPointSummaryResponse summary,
        AssistantTurnResponse turn
) {
}
