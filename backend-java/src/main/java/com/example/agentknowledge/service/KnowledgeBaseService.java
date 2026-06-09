package com.example.agentknowledge.service;

import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.dto.knowledge.CreateKnowledgeBaseRequest;
import com.example.agentknowledge.dto.knowledge.KnowledgeBaseResponse;
import com.example.agentknowledge.dto.knowledge.UpdateKnowledgeBaseRequest;
import com.example.agentknowledge.repository.DocumentChunkRepository;
import com.example.agentknowledge.repository.KnowledgeBaseRepository;
import com.example.agentknowledge.repository.KnowledgeDocumentRepository;
import jakarta.transaction.Transactional;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class KnowledgeBaseService {

    private static final Logger log = LoggerFactory.getLogger(KnowledgeBaseService.class);

    private final KnowledgeBaseRepository knowledgeBaseRepository;
    private final KnowledgeDocumentRepository knowledgeDocumentRepository;
    private final DocumentChunkRepository documentChunkRepository;

    public KnowledgeBaseService(
            KnowledgeBaseRepository knowledgeBaseRepository,
            KnowledgeDocumentRepository knowledgeDocumentRepository,
            DocumentChunkRepository documentChunkRepository
    ) {
        this.knowledgeBaseRepository = knowledgeBaseRepository;
        this.knowledgeDocumentRepository = knowledgeDocumentRepository;
        this.documentChunkRepository = documentChunkRepository;
    }

    public KnowledgeBaseResponse create(CreateKnowledgeBaseRequest request) {
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setName(request.name());
        knowledgeBase.setDescription(request.description());
        knowledgeBase.setOwnerId(request.ownerId());
        knowledgeBase.setDefaultRagStrategy(request.defaultRagStrategy());
        KnowledgeBase saved = knowledgeBaseRepository.save(knowledgeBase);
        log.info("知识库创建成功: knowledgeBaseId={}, name={}, defaultRagStrategy={}",
                saved.getId(), saved.getName(), saved.getDefaultRagStrategy());
        return toResponse(saved, 0, 0);
    }

    public List<KnowledgeBaseResponse> list() {
        return knowledgeBaseRepository.findAll().stream()
                .map(kb -> {
                    long docCount = knowledgeDocumentRepository.countByKnowledgeBase_Id(kb.getId());
                    long chunkCount = documentChunkRepository.countByKnowledgeBase_Id(kb.getId());
                    return toResponse(kb, (int) docCount, (int) chunkCount);
                })
                .toList();
    }

    public KnowledgeBaseResponse getById(UUID id) {
        KnowledgeBase knowledgeBase = getReference(id);
        long docCount = knowledgeDocumentRepository.countByKnowledgeBase_Id(id);
        long chunkCount = documentChunkRepository.countByKnowledgeBase_Id(id);
        return toResponse(knowledgeBase, (int) docCount, (int) chunkCount);
    }

    public KnowledgeBaseResponse update(UUID id, UpdateKnowledgeBaseRequest request) {
        KnowledgeBase knowledgeBase = getReference(id);
        if (request.name() != null) {
            knowledgeBase.setName(request.name());
        }
        if (request.description() != null) {
            knowledgeBase.setDescription(request.description());
        }
        if (request.ownerId() != null) {
            knowledgeBase.setOwnerId(request.ownerId());
        }
        if (request.status() != null) {
            knowledgeBase.setStatus(request.status());
        }
        if (request.defaultRagStrategy() != null) {
            knowledgeBase.setDefaultRagStrategy(request.defaultRagStrategy());
        }
        knowledgeBase = knowledgeBaseRepository.save(knowledgeBase);
        long docCount = knowledgeDocumentRepository.countByKnowledgeBase_Id(id);
        long chunkCount = documentChunkRepository.countByKnowledgeBase_Id(id);
        log.info("知识库更新成功: knowledgeBaseId={}, name={}, status={}, defaultRagStrategy={}",
                knowledgeBase.getId(), knowledgeBase.getName(), knowledgeBase.getStatus(), knowledgeBase.getDefaultRagStrategy());
        return toResponse(knowledgeBase, (int) docCount, (int) chunkCount);
    }

    @Transactional
    public void delete(UUID id) {
        KnowledgeBase knowledgeBase = getReference(id);
        knowledgeBaseRepository.delete(knowledgeBase);
        log.info("知识库删除成功: knowledgeBaseId={}, name={}", id, knowledgeBase.getName());
    }

    public KnowledgeBase getReference(UUID id) {
        return knowledgeBaseRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Knowledge base not found: " + id));
    }

    private KnowledgeBaseResponse toResponse(KnowledgeBase knowledgeBase, Integer documentCount, Integer chunkCount) {
        return new KnowledgeBaseResponse(
                knowledgeBase.getId(),
                knowledgeBase.getName(),
                knowledgeBase.getDescription(),
                knowledgeBase.getOwnerId(),
                knowledgeBase.getStatus(),
                knowledgeBase.getDefaultRagStrategy(),
                documentCount,
                chunkCount,
                knowledgeBase.getCreatedAt(),
                knowledgeBase.getUpdatedAt()
        );
    }
}
