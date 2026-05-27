package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.KnowledgeBase;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KnowledgeBaseRepository extends JpaRepository<KnowledgeBase, UUID> {
}
