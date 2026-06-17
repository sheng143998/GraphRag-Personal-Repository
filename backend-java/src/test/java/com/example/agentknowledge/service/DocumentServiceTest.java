package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.dto.document.CreateDocumentRequest;
import com.example.agentknowledge.dto.document.DocumentResponse;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class DocumentServiceTest {

    private final KnowledgeDocumentRepository documentRepository = mock(KnowledgeDocumentRepository.class);
    private final DocumentChunkRepository chunkRepository = mock(DocumentChunkRepository.class);
    private final KnowledgeBaseService knowledgeBaseService = mock(KnowledgeBaseService.class);
    private final DocumentIngestDispatcher ingestDispatcher = mock(DocumentIngestDispatcher.class);

    private final DocumentService documentService = new DocumentService(
            documentRepository,
            chunkRepository,
            knowledgeBaseService,
            ingestDispatcher
    );

    @AfterEach
    void tearDown() {
        TraceContext.clear();
    }

    @Test
    void createStartsIngestWithPersistedDocumentId() {
        UUID knowledgeBaseId = UUID.randomUUID();
        UUID persistedDocumentId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = knowledgeBase(knowledgeBaseId);
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
        ArgumentCaptor<DocumentIngestMessage> messageCaptor = ArgumentCaptor.forClass(DocumentIngestMessage.class);
        verify(ingestDispatcher).dispatch(messageCaptor.capture());
        DocumentIngestMessage message = messageCaptor.getValue();
        assertThat(message.documentId()).isEqualTo(persistedDocumentId);
        assertThat(message.knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(message.title()).isEqualTo("上传测试");
        assertThat(message.documentType()).isEqualTo("tech_note");
        assertThat(message.traceId()).isEqualTo("trace-document-create");
        assertThat(message.filePayload().filename()).isEqualTo("notes.md");
        assertThat(message.filePayload().contentBase64()).isEqualTo("IyBOb3Rlcw==");
    }

    @Test
    void createBatchSubmitsOneIngestMessagePerDocument() {
        UUID knowledgeBaseId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = knowledgeBase(knowledgeBaseId);
        TraceContext.setTraceId("trace-document-batch");

        when(knowledgeBaseService.getReference(knowledgeBaseId)).thenReturn(knowledgeBase);
        when(documentRepository.save(any(KnowledgeDocument.class))).thenAnswer(invocation -> invocation.getArgument(0));

        List<DocumentResponse> responses = documentService.createBatch(List.of(
                request(knowledgeBaseId, "first.md", "folder/first.md"),
                request(knowledgeBaseId, "second.md", "folder/second.md")
        ));

        assertThat(responses).hasSize(2);
        ArgumentCaptor<DocumentIngestMessage> messageCaptor = ArgumentCaptor.forClass(DocumentIngestMessage.class);
        verify(ingestDispatcher, times(2)).dispatch(messageCaptor.capture());
        assertThat(messageCaptor.getAllValues())
                .extracting(message -> message.filePayload().sourcePath())
                .containsExactly("folder/first.md", "folder/second.md");
        assertThat(messageCaptor.getAllValues())
                .allSatisfy(message -> assertThat(message.traceId()).isEqualTo("trace-document-batch"));
    }

    private KnowledgeBase knowledgeBase(UUID knowledgeBaseId) {
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);
        knowledgeBase.setName("Java 知识库");
        return knowledgeBase;
    }

    private CreateDocumentRequest request(UUID knowledgeBaseId, String fileName, String sourcePath) {
        return new CreateDocumentRequest(
                knowledgeBaseId,
                fileName.replace(".md", ""),
                "TECH_NOTE",
                fileName,
                "md",
                "text/markdown",
                "LOCAL_FOLDER_UPLOAD",
                sourcePath,
                "IyBOb3Rlcw==",
                null,
                Map.of()
        );
    }
}
