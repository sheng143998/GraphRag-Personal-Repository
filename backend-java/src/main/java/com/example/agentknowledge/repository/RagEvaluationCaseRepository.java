package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagEvaluationCase;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagEvaluationCaseRepository extends JpaRepository<RagEvaluationCase, UUID> {

    List<RagEvaluationCase> findByExperiment_IdOrderByUpdatedAtDesc(UUID experimentId);

    List<RagEvaluationCase> findAllByOrderByUpdatedAtDesc();
}
