package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentBatchUploadResponse;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.service.DocumentService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.Valid;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.IntStream;
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
    private final ObjectMapper objectMapper;

    public DocumentController(DocumentService documentService, ObjectMapper objectMapper) {
        this.documentService = documentService;
        this.objectMapper = objectMapper;
    }

    @PostMapping(value = "/upload", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<DocumentResponse> upload(@Valid @RequestBody CreateDocumentRequest request) {
        String content = request.content();
        String contentBase64 = Base64.getEncoder().encodeToString(content.getBytes(StandardCharsets.UTF_8));
        CreateDocumentRequest encodedRequest = new CreateDocumentRequest(
                request.knowledgeBaseId(),
                request.title(),
                request.documentType(),
                request.fileName(),
                request.fileType(),
                request.mimeType(),
                request.sourceType(),
                request.sourcePath(),
                contentBase64,
                request.summary(),
                request.metadata()
        );
        return ApiResponse.success(documentService.create(encodedRequest), TraceContext.getTraceId());
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
        return ApiResponse.success(documentService.create(toCreateRequest(
                knowledgeBaseId,
                title,
                documentType,
                sourceType,
                sourcePath,
                summary,
                parseMetadata(metadata),
                file
        )), TraceContext.getTraceId());
    }

    @PostMapping(value = "/upload/batch", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<DocumentBatchUploadResponse> uploadBatchMultipart(
            @RequestParam UUID knowledgeBaseId,
            @RequestParam(required = false) String title,
            @RequestParam String documentType,
            @RequestParam(required = false) String sourceType,
            @RequestParam(required = false) List<String> relativePaths,
            @RequestParam(required = false) String summary,
            @RequestParam(required = false) String metadata,
            @RequestParam("files") List<MultipartFile> files
    ) {
        if (files == null || files.isEmpty()) {
            throw new IllegalArgumentException("至少需要上传一个文件");
        }

        Map<String, Object> parsedMetadata = parseMetadata(metadata);
        List<CreateDocumentRequest> requests = IntStream.range(0, files.size())
                .mapToObj(index -> {
                    MultipartFile file = files.get(index);
                    String relativePath = resolveRelativePath(relativePaths, index, file);
                    return toCreateRequest(
                            knowledgeBaseId,
                            resolveTitle(title, file, relativePath, files.size()),
                            documentType,
                            sourceType == null || sourceType.isBlank() ? "LOCAL_FOLDER_UPLOAD" : sourceType,
                            relativePath,
                            summary,
                            parsedMetadata,
                            file
                    );
                })
                .toList();

        List<DocumentResponse> documents = documentService.createBatch(requests);
        DocumentBatchUploadResponse response = new DocumentBatchUploadResponse(
                UUID.randomUUID(),
                documents.size(),
                documents
        );
        return ApiResponse.success(response, TraceContext.getTraceId());
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

    private CreateDocumentRequest toCreateRequest(
            UUID knowledgeBaseId,
            String title,
            String documentType,
            String sourceType,
            String sourcePath,
            String summary,
            Map<String, Object> metadata,
            MultipartFile file
    ) {
        String fileName = file.getOriginalFilename() == null || file.getOriginalFilename().isBlank()
                ? "uploaded-document.txt"
                : file.getOriginalFilename();
        try {
            String rawContent = Base64.getEncoder().encodeToString(file.getBytes());
            return new CreateDocumentRequest(
                    knowledgeBaseId,
                    title == null || title.isBlank() ? fileName.replaceFirst("\\.[^.]+$", "") : title,
                    documentType,
                    fileName,
                    inferFileType(fileName),
                    file.getContentType(),
                    sourceType,
                    sourcePath == null || sourcePath.isBlank() ? fileName : sourcePath,
                    rawContent,
                    summary,
                    metadata
            );
        } catch (IOException e) {
            throw new IllegalArgumentException("读取上传文件失败: " + fileName, e);
        }
    }

    private Map<String, Object> parseMetadata(String metadata) {
        if (metadata == null || metadata.isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(metadata, new TypeReference<>() {});
        } catch (IOException e) {
            return Map.of("raw_metadata", metadata);
        }
    }

    private String resolveRelativePath(List<String> relativePaths, int index, MultipartFile file) {
        if (relativePaths != null && index < relativePaths.size()) {
            String value = relativePaths.get(index);
            if (value != null && !value.isBlank()) {
                return normalizePath(value);
            }
        }
        return file.getOriginalFilename() == null || file.getOriginalFilename().isBlank()
                ? "uploaded-document.txt"
                : normalizePath(file.getOriginalFilename());
    }

    private String resolveTitle(String batchTitle, MultipartFile file, String relativePath, int total) {
        if (total == 1 && batchTitle != null && !batchTitle.isBlank()) {
            return batchTitle;
        }
        String name = relativePath == null || relativePath.isBlank() ? file.getOriginalFilename() : relativePath;
        String fileName = name == null || name.isBlank() ? "uploaded-document" : name;
        int slashIndex = Math.max(fileName.lastIndexOf('/'), fileName.lastIndexOf('\\'));
        String leafName = slashIndex >= 0 ? fileName.substring(slashIndex + 1) : fileName;
        return leafName.replaceFirst("\\.[^.]+$", "");
    }

    private String normalizePath(String path) {
        return path.replace('\\', '/');
    }

    private String inferFileType(String fileName) {
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex >= 0 && dotIndex + 1 < fileName.length()) {
            return fileName.substring(dotIndex + 1).toLowerCase();
        }
        return "txt";
    }
}
