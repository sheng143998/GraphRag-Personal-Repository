package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.DocumentChunk;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentChunkRepository extends JpaRepository<DocumentChunk, UUID> {
}
