package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagRun;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagRunRepository extends JpaRepository<RagRun, UUID> {
}
