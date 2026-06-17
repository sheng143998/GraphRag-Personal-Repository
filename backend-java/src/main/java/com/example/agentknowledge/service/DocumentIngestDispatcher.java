package com.example.agentknowledge.service;

import com.example.agentknowledge.config.DocumentIngestQueueProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Service;

@Service
public class DocumentIngestDispatcher {

    private static final Logger log = LoggerFactory.getLogger(DocumentIngestDispatcher.class);

    private final DocumentIngestQueueProperties properties;
    private final DocumentIngestProcessor processor;
    private final RabbitTemplate rabbitTemplate;

    public DocumentIngestDispatcher(
            DocumentIngestQueueProperties properties,
            DocumentIngestProcessor processor,
            ObjectProvider<RabbitTemplate> rabbitTemplateProvider
    ) {
        this.properties = properties;
        this.processor = processor;
        this.rabbitTemplate = rabbitTemplateProvider.getIfAvailable();
    }

    public void dispatch(DocumentIngestMessage message) {
        if (properties.rabbitMqEnabled()) {
            if (rabbitTemplate == null) {
                throw new IllegalStateException("RabbitMQ ingest mode is enabled, but RabbitTemplate is unavailable");
            }
            rabbitTemplate.convertAndSend(properties.exchange(), properties.routingKey(), message);
            log.info("文档入库任务已发布到 RabbitMQ: documentId={}, exchange={}, routingKey={}, traceId={}",
                    message.documentId(), properties.exchange(), properties.routingKey(), message.traceId());
            return;
        }

        processor.processAsync(message);
        log.info("文档入库任务已提交到本地异步线程池: documentId={}, traceId={}", message.documentId(), message.traceId());
    }
}
