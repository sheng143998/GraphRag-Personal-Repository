package com.example.agentknowledge.service;

import com.example.agentknowledge.domain.GraphEntity;
import com.example.agentknowledge.domain.GraphRelationship;
import com.example.agentknowledge.dto.graph.GraphFactsResponse;
import com.example.agentknowledge.repository.GraphEntityRepository;
import com.example.agentknowledge.repository.GraphRelationshipRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GraphFactService {

    private final KnowledgeBaseService knowledgeBaseService;
    private final GraphEntityRepository graphEntityRepository;
    private final GraphRelationshipRepository graphRelationshipRepository;

    public GraphFactService(
            KnowledgeBaseService knowledgeBaseService,
            GraphEntityRepository graphEntityRepository,
            GraphRelationshipRepository graphRelationshipRepository
    ) {
        this.knowledgeBaseService = knowledgeBaseService;
        this.graphEntityRepository = graphEntityRepository;
        this.graphRelationshipRepository = graphRelationshipRepository;
    }

    @Transactional(readOnly = true)
    public GraphFactsResponse getFacts(UUID knowledgeBaseId, String entity) {
        knowledgeBaseService.getReference(knowledgeBaseId);
        String normalizedEntity = normalizeEntityFilter(entity);
        PageRequest limit = PageRequest.of(0, 100);
        List<GraphEntity> entityFacts = normalizedEntity == null
                ? graphEntityRepository.findByKnowledgeBaseIdOrderByCreatedAtDesc(knowledgeBaseId, limit)
                : graphEntityRepository.searchFacts(knowledgeBaseId, normalizedEntity, limit);
        List<GraphRelationship> relationshipFacts = normalizedEntity == null
                ? graphRelationshipRepository.findByKnowledgeBaseIdOrderByCreatedAtDesc(knowledgeBaseId, limit)
                : graphRelationshipRepository.searchFacts(knowledgeBaseId, normalizedEntity, limit);

        List<GraphFactsResponse.EntityFact> entities = entityFacts
                .stream()
                .map(this::toEntityFact)
                .toList();
        List<GraphFactsResponse.RelationshipFact> relationships = relationshipFacts
                .stream()
                .map(this::toRelationshipFact)
                .toList();

        return new GraphFactsResponse(
                knowledgeBaseId,
                normalizedEntity,
                entities.size(),
                relationships.size(),
                entities,
                relationships
        );
    }

    private String normalizeEntityFilter(String entity) {
        if (entity == null || entity.isBlank()) {
            return null;
        }
        return entity.trim();
    }

    private GraphFactsResponse.EntityFact toEntityFact(GraphEntity entity) {
        return new GraphFactsResponse.EntityFact(
                entity.getId(),
                entity.getDocument() == null ? null : entity.getDocument().getId(),
                entity.getChunk() == null ? null : entity.getChunk().getId(),
                entity.getName(),
                entity.getNormalizedName(),
                entity.getEntityType(),
                entity.getAliases(),
                entity.getMetadata(),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    private GraphFactsResponse.RelationshipFact toRelationshipFact(GraphRelationship relationship) {
        return new GraphFactsResponse.RelationshipFact(
                relationship.getId(),
                relationship.getDocument() == null ? null : relationship.getDocument().getId(),
                relationship.getChunk() == null ? null : relationship.getChunk().getId(),
                relationship.getSourceEntity() == null ? null : relationship.getSourceEntity().getId(),
                relationship.getTargetEntity() == null ? null : relationship.getTargetEntity().getId(),
                relationship.getSourceName(),
                relationship.getTargetName(),
                relationship.getRelationType(),
                relationship.getConfidence(),
                relationship.getMetadata(),
                relationship.getCreatedAt()
        );
    }
}
