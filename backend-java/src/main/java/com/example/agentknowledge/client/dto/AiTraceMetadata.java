package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public record AiTraceMetadata(
        @JsonProperty("trace_id") String traceId,
        @JsonProperty("run_id") String runId,
        String operation,
        @JsonProperty("strategy_name") String strategyName,
        @JsonProperty("prompt_name") String promptName,
        @JsonProperty("prompt_version") String promptVersion,
        @JsonProperty("model_name") String modelName,
        String status,
        @JsonProperty("latency_ms") Double latencyMs,
        Map<String, Object> attributes,
        List<Map<String, Object>> steps
) {
}
