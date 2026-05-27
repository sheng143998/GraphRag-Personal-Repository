package com.example.agentknowledge.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.ai-service")
public record AiServiceProperties(
        String baseUrl,
        Duration connectTimeout,
        Duration readTimeout,
        boolean mockEnabled
) {
}
