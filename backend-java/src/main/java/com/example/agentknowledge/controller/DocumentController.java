package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.service.DocumentService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping("/upload")
    public ApiResponse<DocumentResponse> upload(@Valid @RequestBody CreateDocumentRequest request) {
        return ApiResponse.success(documentService.create(request), TraceContext.getTraceId());
    }

    @GetMapping
    public ApiResponse<List<DocumentResponse>> list(@RequestParam(required = false) UUID knowledgeBaseId) {
        return ApiResponse.success(documentService.list(knowledgeBaseId), TraceContext.getTraceId());
    }

    @GetMapping("/{id}")
    public ApiResponse<DocumentResponse> get(@PathVariable UUID id) {
        return ApiResponse.success(documentService.get(id), TraceContext.getTraceId());
    }
}
