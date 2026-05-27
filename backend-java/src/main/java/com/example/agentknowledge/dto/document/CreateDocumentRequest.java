package com.example.agentknowledge.dto.document;

import java.util.UUID;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateDocumentRequest(
        @NotNull UUID knowledgeBaseId,
        @NotBlank @Size(max = 255) String title,
        @NotBlank @Size(max = 50) String documentType,
        @NotBlank @Size(max = 255) String fileName,
        @Size(max = 50) String fileType,
        @Size(max = 100) String mimeType,
        @Size(max = 50) String sourceType,
        @Size(max = 2000) String sourcePath,
        @Size(max = 100) String parserName,
        @Size(max = 50) String parserVersion,
        String summary,
        String metadata
) {
}
