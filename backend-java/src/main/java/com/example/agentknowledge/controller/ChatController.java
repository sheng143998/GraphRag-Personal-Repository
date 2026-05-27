package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.chat.ChatMessageResponse;
import com.example.agentknowledge.dto.chat.ChatSessionResponse;
import com.example.agentknowledge.dto.chat.CreateChatMessageRequest;
import com.example.agentknowledge.dto.chat.CreateChatSessionRequest;
import com.example.agentknowledge.service.ChatService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
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
}
