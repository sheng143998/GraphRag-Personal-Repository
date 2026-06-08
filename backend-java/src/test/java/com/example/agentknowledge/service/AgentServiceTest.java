package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.client.AiServiceGateway;
import com.example.agentknowledge.client.dto.AiAgentInvokeRequest;
import com.example.agentknowledge.client.dto.AiAgentInvokeResponse;
import com.example.agentknowledge.client.dto.AiSourceMetadata;
import com.example.agentknowledge.client.dto.AiTraceMetadata;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.agent.AgentInvokeRequest;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class AgentServiceTest {

    private final AiServiceGateway aiServiceGateway = mock(AiServiceGateway.class);
    private final AgentService agentService = new AgentService(aiServiceGateway);

    @AfterEach
    void clearTrace() {
        TraceContext.clear();
    }

    @Test
    void invokeBridgesRequestToAiAgentAndMapsWorkflowResponse() {
        TraceContext.setTraceId("trace-agent");
        UUID knowledgeBaseId = UUID.randomUUID();
        AiTraceMetadata trace = new AiTraceMetadata(
                "trace-agent",
                "run-agent",
                "agent_invoke",
                "advanced-rag",
                "agent_invoke",
                "v1",
                "stub-llm",
                "completed",
                12.0,
                Map.of("question_type", "implementation")
        );
        when(aiServiceGateway.invokeAgent(org.mockito.ArgumentMatchers.any(AiAgentInvokeRequest.class), eq("trace-agent")))
                .thenReturn(new AiAgentInvokeResponse(
                        "study-agent",
                        "agent answer",
                        List.of(new AiSourceMetadata(null, null, "source", null, 1.0, null, null, null, Map.of())),
                        "implementation",
                        "advanced-rag",
                        List.of(new AiAgentInvokeResponse.WorkflowStep(
                                "select_rag_strategy",
                                "Selected a strategy.",
                                Map.of("selected_strategy_name", "advanced-rag")
                        )),
                        trace
                ));

        var response = agentService.invoke(new AgentInvokeRequest(
                null,
                "How should I implement rerank code?",
                null,
                null,
                knowledgeBaseId,
                null,
                null,
                null,
                null
        ));

        ArgumentCaptor<AiAgentInvokeRequest> requestCaptor = ArgumentCaptor.forClass(AiAgentInvokeRequest.class);
        verify(aiServiceGateway).invokeAgent(requestCaptor.capture(), eq("trace-agent"));
        AiAgentInvokeRequest request = requestCaptor.getValue();

        assertThat(request.agentName()).isEqualTo("study-agent");
        assertThat(request.strategyName()).isEqualTo("basic-rag");
        assertThat(request.topK()).isEqualTo(5);
        assertThat(request.context().knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(request.context().metadataFilters()).isEmpty();
        assertThat(response.selectedStrategyName()).isEqualTo("advanced-rag");
        assertThat(response.workflowSteps()).hasSize(1);
        assertThat(response.workflowSteps().get(0).payload()).containsEntry("selected_strategy_name", "advanced-rag");
    }
}
