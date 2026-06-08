package com.example.agentknowledge.dto.chat;

public record WeakPointPracticeTurnResponse(
        LearningWeakPointResponse weakPoint,
        AssistantTurnResponse turn
) {
}
