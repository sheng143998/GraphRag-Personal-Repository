package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagRetrievalResult;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagRetrievalResultRepository extends JpaRepository<RagRetrievalResult, UUID> {

    List<RagRetrievalResult> findByRunIdOrderByRankAsc(UUID runId);
}
