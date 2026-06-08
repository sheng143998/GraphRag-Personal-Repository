package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.LearningWeakPoint;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface LearningWeakPointRepository extends JpaRepository<LearningWeakPoint, UUID> {

    List<LearningWeakPoint> findTop20BySession_IdOrderByLastSeenAtDesc(UUID sessionId);

    Optional<LearningWeakPoint> findBySession_IdAndTopicIgnoreCase(UUID sessionId, String topic);

    Optional<LearningWeakPoint> findByIdAndSession_Id(UUID id, UUID sessionId);
}
