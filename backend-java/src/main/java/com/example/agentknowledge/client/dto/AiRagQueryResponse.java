package com.example.agentknowledge.client.dto;

import java.util.List;

public record AiRagQueryResponse(
        String question,
        String answer,
        List<AiSourceMetadata> citations,
        AiTraceMetadata trace
) {
}
