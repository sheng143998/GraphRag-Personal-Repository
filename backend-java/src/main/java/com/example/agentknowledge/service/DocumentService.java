package com.example.agentknowledge.service;

import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class DocumentService {

    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);

    private final KnowledgeDocumentRepository knowledgeDocumentRepository;
    private final DocumentChunkRepository documentChunkRepository;
    private final KnowledgeBaseService knowledgeBaseService;
    private final DocumentIngestProcessor ingestProcessor;

    public DocumentService(
            KnowledgeDocumentRepository knowledgeDocumentRepository,
            DocumentChunkRepository documentChunkRepository,
            KnowledgeBaseService knowledgeBaseService,
            DocumentIngestProcessor ingestProcessor
    ) {
        this.knowledgeDocumentRepository = knowledgeDocumentRepository;
        this.documentChunkRepository = documentChunkRepository;
        this.knowledgeBaseService = knowledgeBaseService;
        this.ingestProcessor = ingestProcessor;
    }

    public DocumentResponse create(CreateDocumentRequest request) {
        KnowledgeBase knowledgeBase = knowledgeBaseService.getReference(request.knowledgeBaseId());
        UUID documentId = UUID.randomUUID();
        String fileType = normalizeFileType(request.fileType(), request.fileName());
        Map<String, Object> metadata = request.metadata() == null ? Map.of() : request.metadata();

        String contentBase64 = request.content();

        KnowledgeDocument document = createInitialDocument(request, knowledgeBase, documentId, fileType);
        document = knowledgeDocumentRepository.save(document);
        UUID persistedDocumentId = document.getId();
        log.info("文档元数据已保存，准备提交异步入库任务: documentId={}, knowledgeBaseId={}, title={}, fileName={}, fileType={}",
                persistedDocumentId, knowledgeBase.getId(), request.title(), request.fileName(), fileType);

        AiDocumentIngestRequest.FilePayload filePayload = new AiDocumentIngestRequest.FilePayload(
                request.fileName(),
                fileType,
                null,
                contentBase64,
                request.sourcePath(),
                request.mimeType()
        );

        String traceId = TraceContext.getTraceId();

        ingestProcessor.processAsync(
                persistedDocumentId,
                knowledgeBase.getId(),
                request.title(),
                request.documentType().toLowerCase(),
                filePayload,
                List.of(),
                List.of(),
                metadata,
                traceId
        );
        log.info("文档异步入库任务已提交: documentId={}, traceId={}", persistedDocumentId, traceId);

        return toResponse(document, 0, List.of());
    }

    private KnowledgeDocument createInitialDocument(
            CreateDocumentRequest request,
            KnowledgeBase knowledgeBase,
            UUID documentId,
            String fileType
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
        document.setSummary(request.summary());
        document.setMetadata("{}");
        document.setStatus("PROCESSING");
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
