package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.service.DocumentService;
import jakarta.validation.Valid;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping(value = "/upload", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<DocumentResponse> upload(@Valid @RequestBody CreateDocumentRequest request) {
        return ApiResponse.success(documentService.create(request), TraceContext.getTraceId());
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<DocumentResponse> uploadMultipart(
            @RequestParam UUID knowledgeBaseId,
            @RequestParam String title,
            @RequestParam String documentType,
            @RequestParam(required = false) String sourceType,
            @RequestParam(required = false) String sourcePath,
            @RequestParam(required = false) String summary,
            @RequestParam(required = false) String metadata,
            @RequestParam("file") MultipartFile file
    ) throws IOException {
        String fileName = file.getOriginalFilename() == null || file.getOriginalFilename().isBlank()
                ? "uploaded-document.txt"
                : file.getOriginalFilename();
        // Preserve raw bytes using Base64 instead of corrupting with UTF-8 String
        String rawContent = Base64.getEncoder().encodeToString(file.getBytes());
        CreateDocumentRequest request = new CreateDocumentRequest(
                knowledgeBaseId,
                title,
                documentType,
                fileName,
                inferFileType(fileName),
                file.getContentType(),
                sourceType,
                sourcePath,
                rawContent,
                summary,
                metadata == null || metadata.isBlank() ? Map.of() : Map.of("multipart_metadata", metadata)
        );
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

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable UUID id) {
        documentService.delete(id);
        return ApiResponse.success(null, TraceContext.getTraceId());
    }

    private String inferFileType(String fileName) {
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex >= 0 && dotIndex + 1 < fileName.length()) {
            return fileName.substring(dotIndex + 1).toLowerCase();
        }
        return "txt";
    }
}