package com.example.agentknowledge;

import com.example.agentknowledge.config.AiServiceProperties;
import com.example.agentknowledge.config.DocumentIngestQueueProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties({AiServiceProperties.class, DocumentIngestQueueProperties.class})
public class AgentKnowledgeApplication {

    public static void main(String[] args) {
        SpringApplication.run(AgentKnowledgeApplication.class, args);
    }
}
