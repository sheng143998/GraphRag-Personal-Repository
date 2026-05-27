package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.knowledge.CreateKnowledgeBaseRequest;
import com.example.agentknowledge.dto.knowledge.KnowledgeBaseResponse;
import com.example.agentknowledge.service.KnowledgeBaseService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/knowledge-bases")
public class KnowledgeBaseController {

    private final KnowledgeBaseService knowledgeBaseService;

    public KnowledgeBaseController(KnowledgeBaseService knowledgeBaseService) {
        this.knowledgeBaseService = knowledgeBaseService;
    }

    @PostMapping
    public ApiResponse<KnowledgeBaseResponse> create(@Valid @RequestBody CreateKnowledgeBaseRequest request) {
        return ApiResponse.success(knowledgeBaseService.create(request), TraceContext.getTraceId());
    }

    @GetMapping
    public ApiResponse<List<KnowledgeBaseResponse>> list() {
        return ApiResponse.success(knowledgeBaseService.list(), TraceContext.getTraceId());
    }
}
