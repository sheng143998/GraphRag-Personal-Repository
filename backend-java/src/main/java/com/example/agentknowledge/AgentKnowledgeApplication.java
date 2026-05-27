package com.example.agentknowledge;

import com.example.agentknowledge.config.AiServiceProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(AiServiceProperties.class)
public class AgentKnowledgeApplication {

    public static void main(String[] args) {
        SpringApplication.run(AgentKnowledgeApplication.class, args);
    }
}
