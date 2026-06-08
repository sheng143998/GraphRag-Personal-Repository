package com.example.agentknowledge.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.agentknowledge.domain.GraphEntity;
import com.example.agentknowledge.domain.GraphRelationship;
import com.example.agentknowledge.domain.KnowledgeBase;
import com.example.agentknowledge.dto.graph.GraphFactsResponse;
import com.example.agentknowledge.repository.GraphEntityRepository;
import com.example.agentknowledge.repository.GraphRelationshipRepository;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.data.domain.Pageable;

class GraphFactServiceTest {

    private final KnowledgeBaseService knowledgeBaseService = mock(KnowledgeBaseService.class);
    private final GraphEntityRepository graphEntityRepository = mock(GraphEntityRepository.class);
    private final GraphRelationshipRepository graphRelationshipRepository = mock(GraphRelationshipRepository.class);

    private final GraphFactService graphFactService = new GraphFactService(
            knowledgeBaseService,
            graphEntityRepository,
            graphRelationshipRepository
    );

    @Test
    void getFactsTrimsEntityFilterAndReturnsEntitiesAndRelationships() {
        UUID knowledgeBaseId = UUID.randomUUID();
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setId(knowledgeBaseId);

        GraphEntity entity = new GraphEntity();
        entity.setId(UUID.randomUUID());
        entity.setKnowledgeBase(knowledgeBase);
        entity.setName("GraphRAG");
        entity.setNormalizedName("graphrag");
        entity.setEntityType("concept");
        entity.setAliases("[\"graph rag\"]");
        entity.setMetadata(Map.of("source", "test"));

        GraphRelationship relationship = new GraphRelationship();
        relationship.setId(UUID.randomUUID());
        relationship.setKnowledgeBase(knowledgeBase);
        relationship.setSourceEntity(entity);
        relationship.setSourceName("GraphRAG");
        relationship.setTargetName("RAG");
        relationship.setRelationType("enhances");
        relationship.setConfidence(0.82);
        relationship.setMetadata(Map.of("chunk_index", 1));

        when(knowledgeBaseService.getReference(knowledgeBaseId)).thenReturn(knowledgeBase);
        when(graphEntityRepository.searchFacts(eq(knowledgeBaseId), eq("GraphRAG"), org.mockito.ArgumentMatchers.any(Pageable.class)))
                .thenReturn(List.of(entity));
        when(graphRelationshipRepository.searchFacts(eq(knowledgeBaseId), eq("GraphRAG"), org.mockito.ArgumentMatchers.any(Pageable.class)))
                .thenReturn(List.of(relationship));

        GraphFactsResponse response = graphFactService.getFacts(knowledgeBaseId, "  GraphRAG  ");

        assertThat(response.knowledgeBaseId()).isEqualTo(knowledgeBaseId);
        assertThat(response.entity()).isEqualTo("GraphRAG");
        assertThat(response.entityCount()).isEqualTo(1);
        assertThat(response.relationshipCount()).isEqualTo(1);
        assertThat(response.entities().getFirst().name()).isEqualTo("GraphRAG");
        assertThat(response.entities().getFirst().aliases()).isEqualTo("[\"graph rag\"]");
        assertThat(response.relationships().getFirst().sourceEntityId()).isEqualTo(entity.getId());
        assertThat(response.relationships().getFirst().confidence()).isEqualTo(0.82);

        ArgumentCaptor<Pageable> pageableCaptor = ArgumentCaptor.forClass(Pageable.class);
        verify(graphEntityRepository).searchFacts(eq(knowledgeBaseId), eq("GraphRAG"), pageableCaptor.capture());
        assertThat(pageableCaptor.getValue().getPageSize()).isEqualTo(100);
    }
}
