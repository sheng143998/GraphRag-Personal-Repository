package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import com.example.agentknowledge.client.dto.AiDocumentIngestResponse;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class DocumentIngestProcessorTest {

    private final AiServiceGateway aiServiceGateway = mock(AiServiceGateway.class);
    private final KnowledgeDocumentRepository documentRepository = mock(KnowledgeDocumentRepository.class);

    private final DocumentIngestProcessor processor = new DocumentIngestProcessor(
            aiServiceGateway,
            documentRepository
    );

    @Test
    void processAsyncMarksDocumentIndexedAndStoresParserMetadata() {
        UUID documentId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        KnowledgeDocument document = new KnowledgeDocument();
        document.setId(documentId);
        AiDocumentIngestRequest.FilePayload filePayload = new AiDocumentIngestRequest.FilePayload(
                "notes.md",
                "md",
                "# Notes",
                null,
                null,
                "text/markdown"
        );

        when(aiServiceGateway.ingestDocument(any(AiDocumentIngestRequest.class), eq("trace-1")))
                .thenReturn(new AiDocumentIngestResponse(documentId, 2, "markdown-parser", "md", null));
        when(documentRepository.findById(documentId)).thenReturn(Optional.of(document));

        processor.processAsync(
                documentId,
                knowledgeBaseId,
                "Notes",
                "tech_note",
                filePayload,
                List.of("rag"),
                List.of("spring"),
                Map.of("source", "unit-test"),
                "trace-1"
        );

        ArgumentCaptor<KnowledgeDocument> documentCaptor = ArgumentCaptor.forClass(KnowledgeDocument.class);
        verify(documentRepository).save(documentCaptor.capture());
        KnowledgeDocument savedDocument = documentCaptor.getValue();
        assertThat(savedDocument.getStatus()).isEqualTo("INDEXED");
        assertThat(savedDocument.getParserName()).isEqualTo("markdown-parser");
        assertThat(savedDocument.getParserVersion()).isEqualTo("v1");

        ArgumentCaptor<AiDocumentIngestRequest> requestCaptor = ArgumentCaptor.forClass(AiDocumentIngestRequest.class);
        verify(aiServiceGateway).ingestDocument(requestCaptor.capture(), eq("trace-1"));
        assertThat(requestCaptor.getValue().documentId()).isEqualTo(documentId);
        assertThat(requestCaptor.getValue().knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(requestCaptor.getValue().file()).isSameAs(filePayload);
    }

    @Test
    void processAsyncMarksDocumentFailedAndStoresErrorSummaryWhenAiIngestFails() {
        UUID documentId = UUID.randomUUID();
        UUID knowledgeBaseId = UUID.randomUUID();
        KnowledgeDocument document = new KnowledgeDocument();
        document.setId(documentId);
        RuntimeException failure = new RuntimeException("parser exploded");

        when(aiServiceGateway.ingestDocument(any(AiDocumentIngestRequest.class), eq("trace-failed")))
                .thenThrow(failure);
        when(documentRepository.findById(documentId)).thenReturn(Optional.of(document));

        processor.processAsync(
                documentId,
                knowledgeBaseId,
                "Broken Notes",
                "tech_note",
                new AiDocumentIngestRequest.FilePayload("broken.md", "md", "bad", null, null, "text/markdown"),
                List.of(),
                List.of(),
                Map.of(),
                "trace-failed"
        );

        ArgumentCaptor<KnowledgeDocument> documentCaptor = ArgumentCaptor.forClass(KnowledgeDocument.class);
        verify(documentRepository).save(documentCaptor.capture());
        KnowledgeDocument savedDocument = documentCaptor.getValue();
        assertThat(savedDocument.getStatus()).isEqualTo("FAILED");
        assertThat(savedDocument.getSummary()).contains("parser exploded");
    }
}
