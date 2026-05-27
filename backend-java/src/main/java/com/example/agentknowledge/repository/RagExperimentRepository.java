package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagExperiment;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagExperimentRepository extends JpaRepository<RagExperiment, UUID> {

    List<RagExperiment> findAllByOrderByUpdatedAtDesc();
}
