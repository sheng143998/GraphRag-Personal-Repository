package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.GraphEntity;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface GraphEntityRepository extends JpaRepository<GraphEntity, UUID> {

    List<GraphEntity> findByKnowledgeBaseIdOrderByCreatedAtDesc(UUID knowledgeBaseId, Pageable pageable);

    @Query("""
            select entity from GraphEntity entity
            where entity.knowledgeBase.id = :knowledgeBaseId
              and (lower(entity.name) like lower(concat('%', :entityName, '%'))
                   or lower(entity.normalizedName) like lower(concat('%', :entityName, '%')))
            order by entity.createdAt desc
            """)
    List<GraphEntity> searchFacts(
            @Param("knowledgeBaseId") UUID knowledgeBaseId,
            @Param("entityName") String entityName,
            Pageable pageable
    );
}
