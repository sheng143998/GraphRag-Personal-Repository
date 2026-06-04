package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import com.example.agentknowledge.client.dto.AiDocumentIngestResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.DocumentChunk;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.dto.document.DocumentChunkResponse;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import jakarta.transaction.Transactional;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class DocumentService {

    private final KnowledgeDocumentRepository knowledgeDocumentRepository;
    private final DocumentChunkRepository documentChunkRepository;
    private final KnowledgeBaseService knowledgeBaseService;
    private final AiServiceGateway aiServiceGateway;

    public DocumentService(
            KnowledgeDocumentRepository knowledgeDocumentRepository,
            DocumentChunkRepository documentChunkRepository,
            KnowledgeBaseService knowledgeBaseService,
            AiServiceGateway aiServiceGateway
    ) {
        this.knowledgeDocumentRepository = knowledgeDocumentRepository;
        this.documentChunkRepository = documentChunkRepository;
        this.knowledgeBaseService = knowledgeBaseService;
        this.aiServiceGateway = aiServiceGateway;
    }

    public DocumentResponse create(CreateDocumentRequest request) {
        KnowledgeBase knowledgeBase = knowledgeBaseService.getReference(request.knowledgeBaseId());
        UUID documentId = UUID.randomUUID();
        String fileType = normalizeFileType(request.fileType(), request.fileName());
        Map<String, Object> metadata = request.metadata() == null ? Map.of() : request.metadata();

        // Content from Controller is already Base64-encoded raw bytes
        String contentBase64 = request.content();

        AiDocumentIngestResponse ingestResponse = aiServiceGateway.ingestDocument(
                new AiDocumentIngestRequest(
                        knowledgeBase.getId(),
                        documentId,
                        request.title(),
                        request.documentType().toLowerCase(),
                        new AiDocumentIngestRequest.FilePayload(
                                request.fileName(),
                                fileType,
                                null,
                                contentBase64,
                                request.sourcePath(),
                                request.mimeType()
                        ),
                        List.of(),
                        List.of(),
                        metadata
                ),
                TraceContext.getTraceId()
        );

        KnowledgeDocument document = knowledgeDocumentRepository.findById(documentId)
                .orElseGet(() -> createMockIndexedDocument(request, knowledgeBase, documentId, fileType, ingestResponse));
        document.setParserName(ingestResponse.parserName());
        document.setParserVersion(document.getParserVersion() == null ? "v1" : document.getParserVersion());
        document.setStatus("INDEXED");
        document = knowledgeDocumentRepository.save(document);
        return toResponse(document, ingestResponse.chunkCount(), List.of());
    }

    private KnowledgeDocument createMockIndexedDocument(
            CreateDocumentRequest request,
            KnowledgeBase knowledgeBase,
            UUID documentId,
            String fileType,
            AiDocumentIngestResponse ingestResponse
    ) {
        KnowledgeDocument document = new KnowledgeDocument();
        document.setId(documentId);
        document.setKnowledgeBase(knowledgeBase);
        document.setTitle(request.title());
        document.setDocumentType(request.documentType());
        document.setFileName(request.fileName());
        document.setFileType(fileType);
        document.setMimeType(request.mimeType());
        document.setSourceType(request.sourceType() == null || request.sourceType().isBlank() ? "LOCAL_UPLOAD" : request.sourceType());
        document.setSourcePath(request.sourcePath());
        document.setParserName(ingestResponse.parserName());
        document.setParserVersion("v1");
        document.setSummary(request.summary());
        document.setMetadata("{}");
        document.setStatus("INDEXED");
        return document;
    }

    public List<DocumentResponse> list(UUID knowledgeBaseId) {
        List<KnowledgeDocument> documents = knowledgeBaseId == null
                ? knowledgeDocumentRepository.findAll()
                : knowledgeDocumentRepository.findByKnowledgeBase_IdOrderByCreatedAtDesc(knowledgeBaseId);
        return documents.stream()
                .map(document -> toResponse(
                        document,
                        Math.toIntExact(documentChunkRepository.countByDocument_Id(document.getId())),
                        List.of()
                ))
                .toList();
    }

    public DocumentResponse get(UUID id) {
        KnowledgeDocument document = knowledgeDocumentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found: " + id));
        List<DocumentChunkResponse> chunks = documentChunkRepository.findByDocument_IdOrderByChunkIndexAsc(id)
                .stream()
                .map(this::toChunkResponse)
                .toList();
        return toResponse(document, chunks.size(), chunks);
    }

    @Transactional
    public void delete(UUID id) {
        KnowledgeDocument document = knowledgeDocumentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found: " + id));
        knowledgeDocumentRepository.delete(document);
    }

    private DocumentResponse toResponse(
            KnowledgeDocument document,
            Integer chunkCount,
            List<DocumentChunkResponse> chunks
    ) {
        return new DocumentResponse(
                document.getId(),
                document.getKnowledgeBase().getId(),
                document.getKnowledgeBase().getName(),
                document.getTitle(),
                document.getDocumentType(),
                document.getFileName(),
                document.getFileType(),
                document.getMimeType(),
                document.getSourceType(),
                document.getSourcePath(),
                document.getParserName(),
                document.getParserVersion(),
                document.getStatus(),
                document.getSummary(),
                document.getMetadata(),
                chunkCount,
                chunks,
                document.getCreatedAt(),
                document.getUpdatedAt()
        );
    }

    private DocumentChunkResponse toChunkResponse(DocumentChunk chunk) {
        return new DocumentChunkResponse(
                chunk.getId(),
                chunk.getChunkIndex(),
                chunk.getTitle(),
                preview(chunk.getContent()),
                chunk.getChunkStrategy(),
                chunk.getPageNumber(),
                chunk.getSheetName(),
                chunk.getRowRange(),
                chunk.getMetadata()
        );
    }

    private String preview(String content) {
        if (content == null || content.length() <= 500) {
            return content;
        }
        return content.substring(0, 500);
    }

    private String normalizeFileType(String fileType, String fileName) {
        if (fileType != null && !fileType.isBlank()) {
            return fileType.toLowerCase();
        }
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex >= 0 && dotIndex + 1 < fileName.length()) {
            return fileName.substring(dotIndex + 1).toLowerCase();
        }
        return "txt";
    }
}