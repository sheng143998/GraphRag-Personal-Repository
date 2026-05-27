package com.example.agentknowledge.repository;

import com.example.agentknowledge.domain.ChatSession;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {

    List<ChatSession> findAllByOrderByUpdatedAtDesc();
}
