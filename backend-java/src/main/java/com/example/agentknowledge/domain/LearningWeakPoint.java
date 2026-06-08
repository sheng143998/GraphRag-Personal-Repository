package com.example.agentknowledge.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.annotations.UuidGenerator;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "learning_weak_points")
public class LearningWeakPoint {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "session_id", nullable = false)
    private ChatSession session;

    @ManyToOne
    @JoinColumn(name = "knowledge_base_id")
    private KnowledgeBase knowledgeBase;

    @ManyToOne
    @JoinColumn(name = "evidence_message_id")
    private ChatMessage evidenceMessage;

    @Column(nullable = false, length = 500)
    private String topic;

    @Column(name = "expected_answer", columnDefinition = "TEXT")
    private String expectedAnswer;

    @Column(name = "source_hint", columnDefinition = "TEXT")
    private String sourceHint;

    @Column(nullable = false, length = 32)
    private String difficulty = "medium";

    @Column(name = "review_count", nullable = false)
    private Integer reviewCount = 1;

    @Column(name = "last_seen_at", nullable = false)
    private Instant lastSeenAt;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;
}
