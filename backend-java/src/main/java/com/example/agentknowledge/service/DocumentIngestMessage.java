package com.example.agentknowledge.service;

import com.example.agentknowledge.client.dto.AiDocumentIngestRequest;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record DocumentIngestMessage(
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
}
