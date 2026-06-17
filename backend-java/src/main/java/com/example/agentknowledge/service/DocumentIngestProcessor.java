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
    public void processAsync(DocumentIngestMessage message) {
        process(message);
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
        process(new DocumentIngestMessage(
                documentId,
                knowledgeBaseId,
                title,
                documentType,
                filePayload,
                tags,
                techStack,
                metadata,
                traceId
        ));
    }

    public void process(DocumentIngestMessage message) {
        TraceContext.setTraceId(message.traceId());
        try {
            AiDocumentIngestRequest.FilePayload filePayload = message.filePayload();
            log.info("开始处理文档入库任务: documentId={}, knowledgeBaseId={}, title={}, fileName={}, fileType={}, traceId={}",
                    message.documentId(), message.knowledgeBaseId(), message.title(), filePayload.filename(), filePayload.fileType(), message.traceId());

            String summary = documentRepository.findById(message.documentId())
                    .map(KnowledgeDocument::getSummary)
                    .filter(value -> value != null && !value.isBlank())
                    .orElse(filePayload.filename());
            AiDocumentIngestRequest ingestRequest = new AiDocumentIngestRequest(
                    message.knowledgeBaseId(),
                    message.documentId(),
                    message.title(),
                    message.documentType(),
                    summary,
                    filePayload,
                    safeList(message.tags()),
                    safeList(message.techStack()),
                    safeMap(message.metadata())
            );

            log.info("准备调用 AI 文档入库接口: documentId={}, path=/ai/ingest/document, traceId={}",
                    message.documentId(), message.traceId());
            AiDocumentIngestResponse response = aiServiceGateway.ingestDocument(ingestRequest, message.traceId());
            if (response == null) {
                throw new IllegalStateException("AI document ingest returned empty response");
            }
            if (response.chunkCount() == null || response.chunkCount() <= 0) {
                throw new IllegalStateException("AI document ingest returned no chunks for documentId=" + message.documentId());
            }
            log.info("AI 文档入库接口返回成功: documentId={}, responseDocumentId={}, chunks={}, parser={}, fileType={}, traceId={}",
                    message.documentId(), response.documentId(), response.chunkCount(), response.parserName(), response.fileType(), message.traceId());

            KnowledgeDocument document = documentRepository.findById(message.documentId()).orElse(null);
            if (document != null) {
                document.setStatus("INDEXED");
                document.setParserName(response.parserName());
                if (document.getParserVersion() == null) {
                    document.setParserVersion("v1");
                }
                documentRepository.save(document);
                log.info("文档入库完成，状态已更新为 INDEXED: documentId={}, chunks={}, parser={}, traceId={}",
                        message.documentId(), response.chunkCount(), response.parserName(), message.traceId());
            } else {
                log.warn("AI 入库已完成，但 Java 文档记录不存在，无法更新状态: documentId={}, traceId={}",
                        message.documentId(), message.traceId());
            }
        } catch (Exception e) {
            log.error("文档入库任务失败: documentId={}, traceId={}", message.documentId(), message.traceId(), e);
            KnowledgeDocument document = documentRepository.findById(message.documentId()).orElse(null);
            if (document != null) {
                document.setStatus("FAILED");
                documentRepository.save(document);
                log.info("文档状态已更新为 FAILED: documentId={}, traceId={}", message.documentId(), message.traceId());
            } else {
                log.warn("文档入库任务失败，但 Java 文档记录不存在，无法写入 FAILED 状态: documentId={}, traceId={}",
                        message.documentId(), message.traceId());
            }
        } finally {
            TraceContext.clear();
        }
    }

    private List<String> safeList(List<String> values) {
        return values == null ? List.of() : values;
    }

    private Map<String, Object> safeMap(Map<String, Object> values) {
        return values == null ? Map.of() : values;
    }
}
