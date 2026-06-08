package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagExperimentEvaluation;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagExperimentEvaluationRepository extends JpaRepository<RagExperimentEvaluation, UUID> {

    List<RagExperimentEvaluation> findByExperiment_IdOrderByCreatedAtDesc(UUID experimentId, Pageable pageable);

    List<RagExperimentEvaluation> findAllByOrderByCreatedAtDesc(Pageable pageable);
}
