package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.DocumentChunk;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentChunkRepository extends JpaRepository<DocumentChunk, UUID> {

    long countByDocument_Id(UUID documentId);

    long countByKnowledgeBase_Id(UUID knowledgeBaseId);

    List<DocumentChunk> findByDocument_IdOrderByChunkIndexAsc(UUID documentId);
}
