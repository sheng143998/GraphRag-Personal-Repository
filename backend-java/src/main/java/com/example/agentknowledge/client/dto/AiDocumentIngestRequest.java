package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record AiDocumentIngestRequest(
        @JsonProperty("knowledge_base_id") UUID knowledgeBaseId,
        @JsonProperty("document_id") UUID documentId,
        String title,
        @JsonProperty("document_type") String documentType,
        FilePayload file,
        List<String> tags,
        @JsonProperty("tech_stack") List<String> techStack,
        Map<String, Object> metadata
) {
    public record FilePayload(
            String filename,
            @JsonProperty("file_type") String fileType,
            String content,
            @JsonProperty("content_base64") String contentBase64,
            @JsonProperty("source_path") String sourcePath,
            @JsonProperty("mime_type") String mimeType
    ) {
    }
}