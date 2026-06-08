package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.GraphRelationship;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface GraphRelationshipRepository extends JpaRepository<GraphRelationship, UUID> {

    List<GraphRelationship> findByKnowledgeBaseIdOrderByCreatedAtDesc(UUID knowledgeBaseId, Pageable pageable);

    @Query("""
            select relationship from GraphRelationship relationship
            where relationship.knowledgeBase.id = :knowledgeBaseId
              and (lower(relationship.sourceName) like lower(concat('%', :entityName, '%'))
                   or lower(relationship.targetName) like lower(concat('%', :entityName, '%')))
            order by relationship.createdAt desc
            """)
    List<GraphRelationship> searchFacts(
            @Param("knowledgeBaseId") UUID knowledgeBaseId,
            @Param("entityName") String entityName,
            Pageable pageable
    );
}
