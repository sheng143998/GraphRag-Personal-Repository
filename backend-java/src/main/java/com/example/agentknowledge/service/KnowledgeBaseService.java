package com.example.agentknowledge.service;

import com.example.agentknowledge.common.exception.ResourceNotFoundException;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.dto.knowledge.CreateKnowledgeBaseRequest;
import com.example.agentknowledge.dto.knowledge.KnowledgeBaseResponse;
import com.example.agentknowledge.repository.KnowledgeBaseRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class KnowledgeBaseService {

    private final KnowledgeBaseRepository knowledgeBaseRepository;

    public KnowledgeBaseService(KnowledgeBaseRepository knowledgeBaseRepository) {
        this.knowledgeBaseRepository = knowledgeBaseRepository;
    }

    public KnowledgeBaseResponse create(CreateKnowledgeBaseRequest request) {
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setName(request.name());
        knowledgeBase.setDescription(request.description());
        knowledgeBase.setOwnerId(request.ownerId());
        knowledgeBase.setDefaultRagStrategy(request.defaultRagStrategy());
        return toResponse(knowledgeBaseRepository.save(knowledgeBase));
    }

    public List<KnowledgeBaseResponse> list() {
        return knowledgeBaseRepository.findAll().stream().map(this::toResponse).toList();
    }

    public KnowledgeBase getReference(UUID id) {
        return knowledgeBaseRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Knowledge base not found: " + id));
    }

    private KnowledgeBaseResponse toResponse(KnowledgeBase knowledgeBase) {
        return new KnowledgeBaseResponse(
                knowledgeBase.getId(),
                knowledgeBase.getName(),
                knowledgeBase.getDescription(),
                knowledgeBase.getOwnerId(),
                knowledgeBase.getStatus(),
                knowledgeBase.getDefaultRagStrategy(),
                knowledgeBase.getCreatedAt(),
                knowledgeBase.getUpdatedAt()
        );
    }
}
