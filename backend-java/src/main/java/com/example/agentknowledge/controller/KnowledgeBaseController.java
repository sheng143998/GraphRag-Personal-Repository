package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.knowledge.CreateKnowledgeBaseRequest;
import com.example.agentknowledge.dto.knowledge.KnowledgeBaseResponse;
import com.example.agentknowledge.dto.knowledge.UpdateKnowledgeBaseRequest;
import com.example.agentknowledge.service.KnowledgeBaseService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
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

    @GetMapping("/{id}")
    public ApiResponse<KnowledgeBaseResponse> getById(@PathVariable UUID id) {
        return ApiResponse.success(knowledgeBaseService.getById(id), TraceContext.getTraceId());
    }

    @PutMapping("/{id}")
    public ApiResponse<KnowledgeBaseResponse> update(@PathVariable UUID id, @Valid @RequestBody UpdateKnowledgeBaseRequest request) {
        return ApiResponse.success(knowledgeBaseService.update(id, request), TraceContext.getTraceId());
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable UUID id) {
        knowledgeBaseService.delete(id);
        return ApiResponse.success(null, TraceContext.getTraceId());
    }
}