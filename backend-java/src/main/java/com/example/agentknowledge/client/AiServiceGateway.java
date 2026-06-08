package com.example.agentknowledge.client;

import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import com.example.agentknowledge.client.dto.AiDocumentIngestResponse;
import com.example.agentknowledge.client.dto.AiAgentInvokeRequest;
import com.example.agentknowledge.client.dto.AiAgentInvokeResponse;
import com.example.agentknowledge.client.dto.AiRagQueryRequest;
import com.example.agentknowledge.client.dto.AiRagQueryResponse;

public interface AiServiceGateway {

    AiRagQueryResponse queryRag(AiRagQueryRequest request, String traceId);

    AiAgentInvokeResponse invokeAgent(AiAgentInvokeRequest request, String traceId);

    AiDocumentIngestResponse ingestDocument(AiDocumentIngestRequest request, String traceId);
}
