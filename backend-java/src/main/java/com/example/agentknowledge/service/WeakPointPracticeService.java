package com.example.agentknowledge.service;

import com.example.agentknowledge.domain.LearningWeakPoint;
import com.example.agentknowledge.dto.chat.AssistantTurnResponse;
import com.example.agentknowledge.dto.chat.CreateAssistantTurnRequest;
import com.example.agentknowledge.dto.chat.CreateWeakPointPracticeTurnRequest;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.dto.chat.LearningWeakPointSummaryResponse;
import com.example.agentknowledge.dto.chat.WeakPointPracticeAssessmentResponse;
import com.example.agentknowledge.dto.chat.WeakPointPracticeTurnResponse;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class WeakPointPracticeService {

    private final LearningWeakPointService learningWeakPointService;
    private final AssistantTurnService assistantTurnService;

    public WeakPointPracticeService(
            LearningWeakPointService learningWeakPointService,
            AssistantTurnService assistantTurnService
    ) {
        this.learningWeakPointService = learningWeakPointService;
        this.assistantTurnService = assistantTurnService;
    }

    @Transactional
    public WeakPointPracticeTurnResponse runPracticeTurn(
            UUID sessionId,
            UUID weakPointId,
            CreateWeakPointPracticeTurnRequest request
    ) {
        LearningWeakPoint weakPoint = learningWeakPointService.getWeakPoint(sessionId, weakPointId);
        LearningWeakPointResponse weakPointResponse = learningWeakPointService.toResponse(weakPoint);
        Map<String, Object> variables = new LinkedHashMap<>();
        variables.put("mode", "weak-point-practice");
        variables.put("weakPointId", weakPointResponse.id().toString());
        variables.put("weakPointTopic", weakPointResponse.topic());
        AssistantTurnResponse turn = assistantTurnService.runTurn(sessionId, new CreateAssistantTurnRequest(
                buildPracticePrompt(weakPointResponse, request.userAnswer()),
                "study-agent",
                request.strategyName(),
                request.topK(),
                Map.of(),
                variables
        ));
        LearningWeakPointResponse updatedWeakPoint = weakPointResponse;
        WeakPointPracticeAssessmentResponse assessment = null;
        if (shouldAutoAssess(request)) {
            LearningWeakPointService.PracticeAssessmentResult result =
                    learningWeakPointService.assessPracticeAnswer(sessionId, weakPointId, request.userAnswer());
            updatedWeakPoint = result.updatedWeakPoint();
            assessment = result.assessment();
        }
        LearningWeakPointSummaryResponse summary = learningWeakPointService.summarizeWeakPoints(sessionId);
        return new WeakPointPracticeTurnResponse(weakPointResponse, updatedWeakPoint, assessment, summary, turn);
    }

    private static boolean shouldAutoAssess(CreateWeakPointPracticeTurnRequest request) {
        return request.userAnswer() != null
                && !request.userAnswer().isBlank()
                && !Boolean.FALSE.equals(request.autoAssess());
    }

    private static String buildPracticePrompt(LearningWeakPointResponse weakPoint, String userAnswer) {
        StringBuilder prompt = new StringBuilder()
                .append("Help me practice this weak point: ")
                .append(weakPoint.topic())
                .append(". Ask one interview-style recall question first, then evaluate my answer against the expected answer.");
        if (weakPoint.expectedAnswer() != null && !weakPoint.expectedAnswer().isBlank()) {
            prompt.append(" Expected answer: ").append(weakPoint.expectedAnswer());
        }
        if (weakPoint.sourceHint() != null && !weakPoint.sourceHint().isBlank()) {
            prompt.append(" Source hint: ").append(weakPoint.sourceHint());
        }
        if (userAnswer != null && !userAnswer.isBlank()) {
            prompt.append(" My current answer: ").append(userAnswer.trim());
        }
        return prompt.toString();
    }
}
