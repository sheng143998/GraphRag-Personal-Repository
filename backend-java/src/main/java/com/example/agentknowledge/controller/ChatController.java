package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.chat.ChatMessageResponse;
import com.example.agentknowledge.dto.chat.ChatSessionResponse;
import com.example.agentknowledge.dto.chat.AssistantTurnResponse;
import com.example.agentknowledge.dto.chat.CreateAssistantTurnRequest;
import com.example.agentknowledge.dto.chat.CreateChatMessageRequest;
import com.example.agentknowledge.dto.chat.CreateChatSessionRequest;
import com.example.agentknowledge.dto.chat.CreateWeakPointPracticeTurnRequest;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.dto.chat.UpdateLearningWeakPointRequest;
import com.example.agentknowledge.dto.chat.WeakPointPracticeTurnResponse;
import com.example.agentknowledge.service.AssistantTurnService;
import com.example.agentknowledge.service.ChatService;
import com.example.agentknowledge.service.LearningWeakPointService;
import com.example.agentknowledge.service.WeakPointPracticeService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final ChatService chatService;
    private final AssistantTurnService assistantTurnService;
    private final LearningWeakPointService learningWeakPointService;
    private final WeakPointPracticeService weakPointPracticeService;

    public ChatController(
            ChatService chatService,
            AssistantTurnService assistantTurnService,
            LearningWeakPointService learningWeakPointService,
            WeakPointPracticeService weakPointPracticeService
    ) {
        this.chatService = chatService;
        this.assistantTurnService = assistantTurnService;
        this.learningWeakPointService = learningWeakPointService;
        this.weakPointPracticeService = weakPointPracticeService;
    }

    @PostMapping("/sessions")
    public ApiResponse<ChatSessionResponse> createSession(@Valid @RequestBody CreateChatSessionRequest request) {
        return ApiResponse.success(chatService.createSession(request), TraceContext.getTraceId());
    }

    @GetMapping("/sessions")
    public ApiResponse<List<ChatSessionResponse>> listSessions() {
        return ApiResponse.success(chatService.listSessions(), TraceContext.getTraceId());
    }

    @PostMapping("/{sessionId}/messages")
    public ApiResponse<ChatMessageResponse> addMessage(
            @PathVariable UUID sessionId,
            @Valid @RequestBody CreateChatMessageRequest request
    ) {
        return ApiResponse.success(chatService.addMessage(sessionId, request), TraceContext.getTraceId());
    }

    @GetMapping("/{sessionId}/messages")
    public ApiResponse<List<ChatMessageResponse>> listMessages(@PathVariable UUID sessionId) {
        return ApiResponse.success(chatService.listMessages(sessionId), TraceContext.getTraceId());
    }

    @GetMapping("/{sessionId}/weak-points")
    public ApiResponse<List<LearningWeakPointResponse>> listWeakPoints(@PathVariable UUID sessionId) {
        return ApiResponse.success(learningWeakPointService.listWeakPoints(sessionId), TraceContext.getTraceId());
    }

    @PostMapping("/{sessionId}/weak-points/{weakPointId}/practice-turn")
    public ApiResponse<WeakPointPracticeTurnResponse> practiceWeakPoint(
            @PathVariable UUID sessionId,
            @PathVariable UUID weakPointId,
            @Valid @RequestBody CreateWeakPointPracticeTurnRequest request
    ) {
        return ApiResponse.success(
                weakPointPracticeService.runPracticeTurn(sessionId, weakPointId, request),
                TraceContext.getTraceId()
        );
    }

    @PatchMapping("/{sessionId}/weak-points/{weakPointId}")
    public ApiResponse<LearningWeakPointResponse> updateWeakPoint(
            @PathVariable UUID sessionId,
            @PathVariable UUID weakPointId,
            @Valid @RequestBody UpdateLearningWeakPointRequest request
    ) {
        return ApiResponse.success(
                learningWeakPointService.updateWeakPoint(sessionId, weakPointId, request),
                TraceContext.getTraceId()
        );
    }

    @PostMapping("/{sessionId}/assistant-turn")
    public ApiResponse<AssistantTurnResponse> assistantTurn(
            @PathVariable UUID sessionId,
            @Valid @RequestBody CreateAssistantTurnRequest request
    ) {
        return ApiResponse.success(assistantTurnService.runTurn(sessionId, request), TraceContext.getTraceId());
    }
}
