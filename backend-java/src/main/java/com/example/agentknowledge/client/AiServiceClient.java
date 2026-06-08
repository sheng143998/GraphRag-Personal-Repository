package com.example.agentknowledge.client;

import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import com.example.agentknowledge.client.dto.AiDocumentIngestResponse;
import com.example.agentknowledge.client.dto.AiRagQueryRequest;
import com.example.agentknowledge.client.dto.AiRagQueryResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.config.AiServiceProperties;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class AiServiceClient implements AiServiceGateway {

    private final RestClient restClient;
    private final AiServiceProperties properties;

    public AiServiceClient(RestClient aiRestClient, AiServiceProperties properties) {
        this.restClient = aiRestClient;
        this.properties = properties;
    }

    @Override
    public AiRagQueryResponse queryRag(AiRagQueryRequest request, String traceId) {
        if (properties.mockEnabled()) {
            return new AiRagQueryResponse(
                    request.question(),
                    "Skeleton response from Spring Boot mock AI client.",
                    List.of(new AiSourceMetadata(
                            null,
                            null,
                            "mock://ai-service/rag/query",
                            null,
                            0.0,
                            0.0,
                            null,
                            null,
                            Map.of("content_preview", "Mock AI response without retrieval.")
                    )),
                    new AiTraceMetadata(
                            traceId,
                            null,
                            "rag_query",
                            request.strategyName(),
                            "rag_answer",
                            "v1",
                            "mock-llm",
                            "completed",
                            15.0,
                            Map.of()
                    )
            );
        }

        return restClient.post()
                .uri("/ai/rag/query")
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .header(TraceContext.HEADER_NAME, traceId)
                .body(request)
                .retrieve()
                .body(AiRagQueryResponse.class);
    }

    @Override
    public AiDocumentIngestResponse ingestDocument(AiDocumentIngestRequest request, String traceId) {
        if (properties.mockEnabled()) {
            return new AiDocumentIngestResponse(
                    request.documentId(),
                    1,
                    "spring-mock-ingest",
                    request.file().fileType(),
                    new AiTraceMetadata(
                            traceId,
                            null,
                            "ingest_document",
                            "document-ingest",
                            null,
                            null,
                            "mock-embedding",
                            "completed",
                            10.0,
                            Map.of()
                    )
            );
        }

        return restClient.post()
                .uri("/ai/ingest/document")
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .header(TraceContext.HEADER_NAME, traceId)
                .body(request)
                .retrieve()
                .body(AiDocumentIngestResponse.class);
    }
}