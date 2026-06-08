package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagRun;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagRunRepository extends JpaRepository<RagRun, UUID> {

    List<RagRun> findAllByOrderByCreatedAtDesc(Pageable pageable);
}
