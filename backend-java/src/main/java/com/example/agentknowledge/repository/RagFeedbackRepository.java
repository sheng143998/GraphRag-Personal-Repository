package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.RagFeedback;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RagFeedbackRepository extends JpaRepository<RagFeedback, UUID> {
}
