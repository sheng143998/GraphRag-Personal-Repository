package com.example.agentknowledge.service;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import com.example.agentknowledge.client.dto.AiDocumentIngestResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.domain.KnowledgeDocument;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

@Component
public class DocumentIngestProcessor {

    private static final Logger log = LoggerFactory.getLogger(DocumentIngestProcessor.class);

    private final AiServiceGateway aiServiceGateway;
    private final KnowledgeDocumentRepository documentRepository;

    public DocumentIngestProcessor(
            AiServiceGateway aiServiceGateway,
            KnowledgeDocumentRepository documentRepository
    ) {
        this.aiServiceGateway = aiServiceGateway;
        this.documentRepository = documentRepository;
    }

    @Async
    public void processAsync(
            UUID documentId,
            UUID knowledgeBaseId,
            String title,
            String documentType,
            AiDocumentIngestRequest.FilePayload filePayload,
            List<String> tags,
            List<String> techStack,
            Map<String, Object> metadata,
            String traceId
    ) {
        TraceContext.setTraceId(traceId);
        try {
            log.info("开始后台处理文档: documentId={}, title={}", documentId, title);
            AiDocumentIngestRequest ingestRequest = new AiDocumentIngestRequest(
                    knowledgeBaseId, documentId, title, documentType,
                    filePayload, tags, techStack, metadata
            );

            AiDocumentIngestResponse response = aiServiceGateway.ingestDocument(ingestRequest, traceId);

            KnowledgeDocument document = documentRepository.findById(documentId).orElse(null);
            if (document != null) {
                document.setStatus("INDEXED");
                document.setParserName(response.parserName());
                if (document.getParserVersion() == null) {
                    document.setParserVersion("v1");
                }
                documentRepository.save(document);
                log.info("文档后台处理完成: documentId={}, chunks={}, parser={}",
                        documentId, response.chunkCount(), response.parserName());
            } else {
                log.warn("后台处理完成但未找到文档记录: documentId={}", documentId);
            }
        } catch (Exception e) {
            log.error("文档后台处理失败: documentId={}", documentId, e);
            KnowledgeDocument document = documentRepository.findById(documentId).orElse(null);
            if (document != null) {
                document.setStatus("FAILED");
                String errorMsg = e.getMessage();
                if (errorMsg != null && errorMsg.length() > 500) {
                    errorMsg = errorMsg.substring(0, 500);
                }
                document.setSummary("解析失败: " + (errorMsg != null ? errorMsg : "未知错误"));
                documentRepository.save(document);
            }
        } finally {
            TraceContext.clear();
        }
    }
}
