package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.KnowledgeDocument;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KnowledgeDocumentRepository extends JpaRepository<KnowledgeDocument, UUID> {

    List<KnowledgeDocument> findByKnowledgeBase_IdOrderByCreatedAtDesc(UUID knowledgeBaseId);
}
