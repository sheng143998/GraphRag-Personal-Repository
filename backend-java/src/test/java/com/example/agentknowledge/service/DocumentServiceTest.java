package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class DocumentServiceTest {

    private final KnowledgeDocumentRepository documentRepository = mock(KnowledgeDocumentRepository.class);
    private final DocumentChunkRepository chunkRepository = mock(DocumentChunkRepository.class);
    private final KnowledgeBaseService knowledgeBaseService = mock(KnowledgeBaseService.class);
    private final DocumentIngestProcessor ingestProcessor = mock(DocumentIngestProcessor.class);

    private final DocumentService documentService = new DocumentService(
            documentRepository,
            chunkRepository,
            knowledgeBaseService,
            ingestProcessor
    );

    @AfterEach
    void tearDown() {
        TraceContext.clear();
    }

    @Test
    void createStartsIngestWithPersistedDocumentId() {
        UUID knowledgeBaseId = UUID.randomUUID();
        UUID persistedDocumentId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        knowledgeBase.setName("Java 知识库");
        TraceContext.setTraceId("trace-document-create");

        when(knowledgeBaseService.getReference(knowledgeBaseId)).thenReturn(knowledgeBase);
        when(documentRepository.save(any(KnowledgeDocument.class))).thenAnswer(invocation -> {
            KnowledgeDocument document = invocation.getArgument(0);
            document.setId(persistedDocumentId);
            return document;
        });

        DocumentResponse response = documentService.create(new CreateDocumentRequest(
                knowledgeBaseId,
                "上传测试",
                "TECH_NOTE",
                "notes.md",
                "md",
                "text/markdown",
                "LOCAL_UPLOAD",
                null,
                "IyBOb3Rlcw==",
                null,
                Map.of()
        ));

        assertThat(response.id()).isEqualTo(persistedDocumentId);
        ArgumentCaptor<UUID> documentIdCaptor = ArgumentCaptor.forClass(UUID.class);
        verify(ingestProcessor).processAsync(
                documentIdCaptor.capture(),
                eq(knowledgeBaseId),
                eq("上传测试"),
                eq("tech_note"),
                any(),
                eq(java.util.List.of()),
                eq(java.util.List.of()),
                eq(Map.of()),
                eq("trace-document-create")
        );
        assertThat(documentIdCaptor.getValue()).isEqualTo(persistedDocumentId);
    }
}
