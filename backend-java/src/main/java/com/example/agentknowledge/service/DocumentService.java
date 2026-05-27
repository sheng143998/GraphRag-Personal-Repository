package com.example.agentknowledge.service;

import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class DocumentService {

    private final KnowledgeDocumentRepository knowledgeDocumentRepository;
    private final KnowledgeBaseService knowledgeBaseService;

    public DocumentService(
            KnowledgeDocumentRepository knowledgeDocumentRepository,
            KnowledgeBaseService knowledgeBaseService
    ) {
        this.knowledgeDocumentRepository = knowledgeDocumentRepository;
        this.knowledgeBaseService = knowledgeBaseService;
    }

    public DocumentResponse create(CreateDocumentRequest request) {
        KnowledgeBase knowledgeBase = knowledgeBaseService.getReference(request.knowledgeBaseId());
        KnowledgeDocument document = new KnowledgeDocument();
        document.setKnowledgeBase(knowledgeBase);
        document.setTitle(request.title());
        document.setDocumentType(request.documentType());
        document.setFileName(request.fileName());
        document.setFileType(request.fileType());
        document.setMimeType(request.mimeType());
        document.setSourceType(request.sourceType() == null || request.sourceType().isBlank() ? "LOCAL_UPLOAD" : request.sourceType());
        document.setSourcePath(request.sourcePath());
        document.setParserName(request.parserName());
        document.setParserVersion(request.parserVersion());
        document.setSummary(request.summary());
        document.setMetadata(request.metadata() == null || request.metadata().isBlank() ? "{}" : request.metadata());
        document.setStatus("UPLOADED");
        return toResponse(knowledgeDocumentRepository.save(document));
    }

    public List<DocumentResponse> list(UUID knowledgeBaseId) {
        List<KnowledgeDocument> documents = knowledgeBaseId == null
                ? knowledgeDocumentRepository.findAll()
                : knowledgeDocumentRepository.findByKnowledgeBase_IdOrderByCreatedAtDesc(knowledgeBaseId);
        return documents.stream().map(this::toResponse).toList();
    }

    public DocumentResponse get(UUID id) {
        return toResponse(knowledgeDocumentRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found: " + id)));
    }

    private DocumentResponse toResponse(KnowledgeDocument document) {
        return new DocumentResponse(
                document.getId(),
                document.getKnowledgeBase().getId(),
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
                document.getCreatedAt(),
                document.getUpdatedAt()
        );
    }
}
