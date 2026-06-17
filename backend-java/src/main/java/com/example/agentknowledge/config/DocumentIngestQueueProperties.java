package com.example.agentknowledge.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.document-ingest")
public record DocumentIngestQueueProperties(
        String mode,
        String exchange,
        String queue,
        String routingKey
) {
    public boolean rabbitMqEnabled() {
        return "rabbitmq".equalsIgnoreCase(mode);
    }
}
