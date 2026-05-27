package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/settings")
public class SettingsController {

    private final String aiServiceBaseUrl;

    public SettingsController(@Value("${app.ai-service.base-url}") String aiServiceBaseUrl) {
        this.aiServiceBaseUrl = aiServiceBaseUrl;
    }

    @GetMapping
    public ApiResponse<Map<String, Object>> getSettings() {
        return ApiResponse.success(Map.of(
                "apiBaseUrl", "/api",
                "aiServiceBaseUrl", aiServiceBaseUrl,
                "defaultKnowledgeBaseId", "",
                "timeoutMs", 15000,
                "includeTraceHeader", true
        ), TraceContext.getTraceId());
    }
}
