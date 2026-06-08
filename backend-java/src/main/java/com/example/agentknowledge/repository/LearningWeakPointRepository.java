package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.LearningWeakPoint;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface LearningWeakPointRepository extends JpaRepository<LearningWeakPoint, UUID> {

    List<LearningWeakPoint> findTop20BySession_IdOrderByLastSeenAtDesc(UUID sessionId);

    List<LearningWeakPoint> findBySession_Id(UUID sessionId);

    @Query("""
            select weakPoint from LearningWeakPoint weakPoint
            where weakPoint.session.id = :sessionId
            order by
                case when weakPoint.masteryStatus = 'NEEDS_REVIEW' then 0 else 1 end,
                case weakPoint.difficulty
                    when 'hard' then 0
                    when 'medium' then 1
                    else 2
                end,
                weakPoint.reviewCount desc,
                weakPoint.lastSeenAt desc
            """)
    List<LearningWeakPoint> findPrioritizedBySessionId(@Param("sessionId") UUID sessionId, Pageable pageable);

    Optional<LearningWeakPoint> findBySession_IdAndTopicIgnoreCase(UUID sessionId, String topic);

    Optional<LearningWeakPoint> findByIdAndSession_Id(UUID id, UUID sessionId);
}
