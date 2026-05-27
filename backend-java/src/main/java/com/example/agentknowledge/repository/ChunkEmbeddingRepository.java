package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.ChunkEmbedding;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChunkEmbeddingRepository extends JpaRepository<ChunkEmbedding, UUID> {
}
