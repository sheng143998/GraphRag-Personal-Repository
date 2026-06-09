package com.example.agentknowledge.client;

import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import com.example.agentknowledge.client.dto.AiDocumentIngestResponse;
import com.example.agentknowledge.client.dto.AiAgentInvokeRequest;
import com.example.agentknowledge.client.dto.AiAgentInvokeResponse;
import com.example.agentknowledge.client.dto.AiRagEvaluateRequest;
import com.example.agentknowledge.client.dto.AiRagEvaluateResponse;
import com.example.agentknowledge.client.dto.AiRagQueryRequest;
import com.example.agentknowledge.client.dto.AiRagQueryResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.config.AiServiceProperties;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class AiServiceClient implements AiServiceGateway {

    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);

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
                            Map.of(),
                            List.of()
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
    public AiRagEvaluateResponse evaluateRag(AiRagEvaluateRequest request, String traceId) {
        if (properties.mockEnabled()) {
            double retrievalScore = request.citations() == null || request.citations().isEmpty() ? 0.0 : 0.8;
            double groundedScore = request.generatedAnswer() == null || request.generatedAnswer().isBlank() ? 0.2 : 0.9;
            return new AiRagEvaluateResponse(
                    new AiRagEvaluateResponse.Result(
                            groundedScore,
                            retrievalScore,
                            List.of("Mock evaluator scored persisted RAG run evidence.")
                    ),
                    new AiTraceMetadata(
                            traceId,
                            null,
                            "rag_evaluate",
                            request.strategyName(),
                            null,
                            null,
                            "mock-evaluator",
                            "completed",
                            8.0,
                            Map.of(),
                            List.of()
                    )
            );
        }

        return restClient.post()
                .uri("/ai/rag/evaluate")
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .header(TraceContext.HEADER_NAME, traceId)
                .body(request)
                .retrieve()
                .body(AiRagEvaluateResponse.class);
    }

    @Override
    public AiAgentInvokeResponse invokeAgent(AiAgentInvokeRequest request, String traceId) {
        if (properties.mockEnabled()) {
            return new AiAgentInvokeResponse(
                    request.agentName(),
                    "Skeleton response from Spring Boot mock AI agent.",
                    List.of(new AiSourceMetadata(
                            null,
                            null,
                            "mock://ai-service/agent/invoke",
                            null,
                            0.0,
                            0.0,
                            null,
                            null,
                            Map.of("content_preview", "Mock AI agent response without retrieval.")
                    )),
                    "general",
                    request.strategyName(),
                    List.of("What should I review next about this topic?"),
                    new AiAgentInvokeResponse.StudyPlan(
                            "Review this topic with one cited source.",
                            List.of("general", request.strategyName()),
                            List.of("Read the answer.", "Check one source.", "Ask one follow-up.")
                    ),
                    List.of(new AiAgentInvokeResponse.ReviewCard(
                            "What is the core idea?",
                            "Explain the concept and cite one supporting source.",
                            "mock-source",
                            "easy"
                    )),
                    List.of(
                            new AiAgentInvokeResponse.WorkflowStep(
                                    "mock_agent_invoke",
                                    "Mocked agent workflow response.",
                                    Map.of("citation_count", 1)
                            )
                    ),
                    new AiTraceMetadata(
                            traceId,
                            null,
                            "agent_invoke",
                            request.strategyName(),
                            "agent_invoke",
                            "v1",
                            "mock-llm",
                            "completed",
                            15.0,
                            Map.of("selected_strategy_name", request.strategyName()),
                            List.of()
                    ),
                    new AiTraceMetadata(
                            traceId,
                            null,
                            "rag_query",
                            request.strategyName(),
                            "rag_answer",
                            "v1",
                            "mock-llm",
                            "completed",
                            12.0,
                            Map.of("rewritten_query", request.userInput()),
                            List.of()
                    )
            );
        }

        log.info("准备调用 AI Agent 接口: path=/ai/agent/invoke, agentName={}, strategyName={}, topK={}, traceId={}",
                request.agentName(), request.strategyName(), request.topK(), traceId);
        AiAgentInvokeResponse response = restClient.post()
                .uri("/ai/agent/invoke")
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .header(TraceContext.HEADER_NAME, traceId)
                .body(request)
                .retrieve()
                .body(AiAgentInvokeResponse.class);
        log.info("AI Agent 接口返回成功: agentName={}, selectedStrategyName={}, citationCount={}, traceId={}",
                response.agentName(),
                response.selectedStrategyName(),
                response.citations() == null ? 0 : response.citations().size(),
                traceId);
        return response;
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
                            Map.of(),
                            List.of()
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
