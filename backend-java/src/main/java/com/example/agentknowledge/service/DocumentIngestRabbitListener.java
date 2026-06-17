package com.example.agentknowledge.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix = "app.document-ingest", name = "mode", havingValue = "rabbitmq")
public class DocumentIngestRabbitListener {

    private static final Logger log = LoggerFactory.getLogger(DocumentIngestRabbitListener.class);

    private final DocumentIngestProcessor processor;

    public DocumentIngestRabbitListener(DocumentIngestProcessor processor) {
        this.processor = processor;
    }

    @RabbitListener(queues = "${app.document-ingest.queue}", containerFactory = "rabbitListenerContainerFactory")
    public void consume(DocumentIngestMessage message) {
        log.info("收到 RabbitMQ 文档入库任务: documentId={}, traceId={}", message.documentId(), message.traceId());
        processor.process(message);
    }
}
