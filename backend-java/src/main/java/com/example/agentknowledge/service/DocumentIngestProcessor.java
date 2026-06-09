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
            log.info("开始异步处理文档入库: documentId={}, knowledgeBaseId={}, title={}, fileName={}, fileType={}, traceId={}",
                    documentId, knowledgeBaseId, title, filePayload.filename(), filePayload.fileType(), traceId);
            AiDocumentIngestRequest ingestRequest = new AiDocumentIngestRequest(
                    knowledgeBaseId, documentId, title, documentType,
                    filePayload, tags, techStack, metadata
            );

            log.info("准备调用 AI 文档入库接口: documentId={}, path=/ai/ingest/document, traceId={}", documentId, traceId);
            AiDocumentIngestResponse response = aiServiceGateway.ingestDocument(ingestRequest, traceId);
            log.info("AI 文档入库接口返回成功: documentId={}, responseDocumentId={}, chunks={}, parser={}, fileType={}, traceId={}",
                    documentId, response.documentId(), response.chunkCount(), response.parserName(), response.fileType(), traceId);

            KnowledgeDocument document = documentRepository.findById(documentId).orElse(null);
            if (document != null) {
                document.setStatus("INDEXED");
                document.setParserName(response.parserName());
                if (document.getParserVersion() == null) {
                    document.setParserVersion("v1");
                }
                documentRepository.save(document);
                log.info("文档异步入库完成，状态已更新为 INDEXED: documentId={}, chunks={}, parser={}, traceId={}",
                        documentId, response.chunkCount(), response.parserName(), traceId);
            } else {
                log.warn("AI 入库已完成，但 Java 文档记录不存在，无法更新状态: documentId={}, traceId={}", documentId, traceId);
            }
        } catch (Exception e) {
            log.error("文档异步入库失败: documentId={}, traceId={}", documentId, traceId, e);
            KnowledgeDocument document = documentRepository.findById(documentId).orElse(null);
            if (document != null) {
                document.setStatus("FAILED");
                String errorMsg = e.getMessage();
                if (errorMsg != null && errorMsg.length() > 500) {
                    errorMsg = errorMsg.substring(0, 500);
                }
                document.setSummary("解析失败: " + (errorMsg != null ? errorMsg : "未知错误"));
                documentRepository.save(document);
                log.info("文档状态已更新为 FAILED: documentId={}, traceId={}", documentId, traceId);
            } else {
                log.warn("文档异步入库失败，但 Java 文档记录不存在，无法写入 FAILED 状态: documentId={}, traceId={}", documentId, traceId);
            }
        } finally {
            TraceContext.clear();
        }
    }
}
