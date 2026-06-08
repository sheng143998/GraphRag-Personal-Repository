package com.example.agentknowledge.service;

import com.example.agentknowledge.domain.ChatMessage;
import com.example.agentknowledge.domain.ChatSession;
import com.example.agentknowledge.domain.LearningWeakPoint;
import com.example.agentknowledge.dto.agent.AgentInvokeResponse;
import com.example.agentknowledge.dto.chat.LearningWeakPointResponse;
import com.example.agentknowledge.dto.chat.LearningWeakPointSummaryResponse;
import com.example.agentknowledge.dto.chat.UpdateLearningWeakPointRequest;
import com.example.agentknowledge.dto.chat.WeakPointPracticeAssessmentResponse;
import com.example.agentknowledge.repository.LearningWeakPointRepository;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LearningWeakPointService {

    private static final Pattern TOKEN_PATTERN = Pattern.compile("[\\p{IsAlphabetic}\\p{IsDigit}][\\p{IsAlphabetic}\\p{IsDigit}_-]*");
    private static final double PASS_THRESHOLD = 0.65;

    private final LearningWeakPointRepository learningWeakPointRepository;
    private final ChatService chatService;

    public LearningWeakPointService(
            LearningWeakPointRepository learningWeakPointRepository,
            ChatService chatService
    ) {
        this.learningWeakPointRepository = learningWeakPointRepository;
        this.chatService = chatService;
    }

    @Transactional
    public List<LearningWeakPointResponse> recordReviewCards(
            ChatSession session,
            ChatMessage evidenceMessage,
            List<AgentInvokeResponse.ReviewCard> reviewCards
    ) {
        if (reviewCards == null || reviewCards.isEmpty()) {
            return listWeakPoints(session.getId());
        }
        for (AgentInvokeResponse.ReviewCard card : reviewCards) {
            String topic = normalizeTopic(card.question());
            if (topic.isBlank()) {
                continue;
            }
            LearningWeakPoint weakPoint = learningWeakPointRepository
                    .findBySession_IdAndTopicIgnoreCase(session.getId(), topic)
                    .orElseGet(() -> createWeakPoint(session, topic));
            weakPoint.setKnowledgeBase(session.getKnowledgeBase());
            weakPoint.setEvidenceMessage(evidenceMessage);
            weakPoint.setExpectedAnswer(card.expectedAnswer());
            weakPoint.setSourceHint(card.sourceHint() != null ? card.sourceHint() : "");
            weakPoint.setDifficulty(card.difficulty() != null && !card.difficulty().isBlank() ? card.difficulty() : "medium");
            weakPoint.setReviewCount(weakPoint.getId() == null ? 1 : weakPoint.getReviewCount() + 1);
            weakPoint.setLastSeenAt(Instant.now());
            if (weakPoint.getNextReviewAt() == null) {
                weakPoint.setNextReviewAt(Instant.now());
            }
            learningWeakPointRepository.save(weakPoint);
        }
        return listWeakPoints(session.getId());
    }

    @Transactional(readOnly = true)
    public List<LearningWeakPointResponse> listWeakPoints(UUID sessionId) {
        chatService.getSession(sessionId);
        return learningWeakPointRepository.findPrioritizedBySessionId(sessionId, PageRequest.of(0, 20))
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public LearningWeakPointSummaryResponse summarizeWeakPoints(UUID sessionId) {
        chatService.getSession(sessionId);
        List<LearningWeakPoint> weakPoints = learningWeakPointRepository.findBySession_Id(sessionId);
        int totalCount = weakPoints.size();
        int needsReviewCount = (int) weakPoints.stream()
                .filter(weakPoint -> "NEEDS_REVIEW".equals(weakPoint.getMasteryStatus()))
                .count();
        int masteredCount = (int) weakPoints.stream()
                .filter(weakPoint -> "MASTERED".equals(weakPoint.getMasteryStatus()))
                .count();
        int hardCount = (int) weakPoints.stream()
                .filter(weakPoint -> "hard".equalsIgnoreCase(weakPoint.getDifficulty()))
                .count();
        Instant now = Instant.now();
        int dueReviewCount = (int) weakPoints.stream()
                .filter(weakPoint -> weakPoint.getNextReviewAt() == null || !weakPoint.getNextReviewAt().isAfter(now))
                .count();
        int totalReviewCount = weakPoints.stream()
                .map(LearningWeakPoint::getReviewCount)
                .filter(java.util.Objects::nonNull)
                .mapToInt(Integer::intValue)
                .sum();
        double completionRate = totalCount == 0 ? 0.0 : (double) masteredCount / totalCount;
        LearningWeakPointResponse nextWeakPoint = learningWeakPointRepository
                .findPrioritizedBySessionId(sessionId, PageRequest.of(0, 1))
                .stream()
                .findFirst()
                .map(this::toResponse)
                .orElse(null);
        return new LearningWeakPointSummaryResponse(
                totalCount,
                needsReviewCount,
                masteredCount,
                hardCount,
                totalReviewCount,
                dueReviewCount,
                completionRate,
                nextWeakPoint
        );
    }

    @Transactional
    public LearningWeakPointResponse updateWeakPoint(
            UUID sessionId,
            UUID weakPointId,
            UpdateLearningWeakPointRequest request
    ) {
        chatService.getSession(sessionId);
        LearningWeakPoint weakPoint = learningWeakPointRepository.findByIdAndSession_Id(weakPointId, sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Learning weak point not found: " + weakPointId));
        String status = normalizeMasteryStatus(request.masteryStatus());
        weakPoint.setMasteryStatus(status);
        Instant now = Instant.now();
        weakPoint.setLastAssessedAt(now);
        if ("MASTERED".equals(status)) {
            weakPoint.setDifficulty("easy");
            weakPoint.setNextReviewAt(now.plus(7, ChronoUnit.DAYS));
        } else {
            weakPoint.setNextReviewAt(now);
        }
        return toResponse(learningWeakPointRepository.save(weakPoint));
    }

    @Transactional
    public PracticeAssessmentResult assessPracticeAnswer(
            UUID sessionId,
            UUID weakPointId,
            String userAnswer
    ) {
        chatService.getSession(sessionId);
        LearningWeakPoint weakPoint = learningWeakPointRepository.findByIdAndSession_Id(weakPointId, sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Learning weak point not found: " + weakPointId));
        double score = answerScore(weakPoint.getExpectedAnswer(), userAnswer);
        boolean passed = score >= PASS_THRESHOLD;
        String masteryStatus = passed ? "MASTERED" : "NEEDS_REVIEW";
        String difficulty = passed ? "easy" : score < 0.35 ? "hard" : "medium";
        weakPoint.setMasteryStatus(masteryStatus);
        weakPoint.setDifficulty(difficulty);
        weakPoint.setReviewCount((weakPoint.getReviewCount() == null ? 0 : weakPoint.getReviewCount()) + 1);
        weakPoint.setPracticeCount((weakPoint.getPracticeCount() == null ? 0 : weakPoint.getPracticeCount()) + 1);
        weakPoint.setLastPracticeScore(score);
        Instant now = Instant.now();
        weakPoint.setLastSeenAt(now);
        weakPoint.setLastAssessedAt(now);
        weakPoint.setNextReviewAt(nextReviewAt(now, score, passed));
        LearningWeakPoint saved = learningWeakPointRepository.save(weakPoint);
        WeakPointPracticeAssessmentResponse assessment = new WeakPointPracticeAssessmentResponse(
                score,
                passed,
                masteryStatus,
                difficulty,
                assessmentFeedback(score, passed)
        );
        return new PracticeAssessmentResult(toResponse(saved), assessment);
    }

    @Transactional(readOnly = true)
    public LearningWeakPoint getWeakPoint(UUID sessionId, UUID weakPointId) {
        chatService.getSession(sessionId);
        return learningWeakPointRepository.findByIdAndSession_Id(weakPointId, sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Learning weak point not found: " + weakPointId));
    }

    private LearningWeakPoint createWeakPoint(ChatSession session, String topic) {
        LearningWeakPoint weakPoint = new LearningWeakPoint();
        weakPoint.setSession(session);
        weakPoint.setTopic(topic);
        weakPoint.setReviewCount(0);
        weakPoint.setPracticeCount(0);
        weakPoint.setNextReviewAt(Instant.now());
        return weakPoint;
    }

    private static String normalizeTopic(String value) {
        return value == null ? "" : value.trim().replaceAll("\\s+", " ");
    }

    private static String normalizeMasteryStatus(String value) {
        String status = value == null ? "" : value.trim().toUpperCase();
        if (!status.equals("MASTERED") && !status.equals("NEEDS_REVIEW")) {
            throw new IllegalArgumentException("Unsupported masteryStatus: " + value);
        }
        return status;
    }

    private static double answerScore(String expectedAnswer, String userAnswer) {
        if (userAnswer == null || userAnswer.isBlank()) {
            return 0.0;
        }
        Set<String> expectedTokens = contentTokens(expectedAnswer);
        Set<String> answerTokens = contentTokens(userAnswer);
        if (expectedTokens.isEmpty()) {
            return answerTokens.isEmpty() ? 0.0 : 0.5;
        }
        if (answerTokens.isEmpty()) {
            return 0.0;
        }
        long hits = expectedTokens.stream()
                .filter(answerTokens::contains)
                .count();
        return (double) hits / expectedTokens.size();
    }

    private static Set<String> contentTokens(String value) {
        if (value == null || value.isBlank()) {
            return Set.of();
        }
        Set<String> tokens = new LinkedHashSet<>();
        var matcher = TOKEN_PATTERN.matcher(value.toLowerCase(Locale.ROOT));
        while (matcher.find()) {
            String token = matcher.group();
            if (token.length() > 2) {
                tokens.add(token);
            }
        }
        if (!tokens.isEmpty()) {
            return tokens;
        }
        return new LinkedHashSet<>(Arrays.asList(value.trim().toLowerCase(Locale.ROOT).split("\\s+")));
    }

    private static String assessmentFeedback(double score, boolean passed) {
        int percent = (int) Math.round(score * 100);
        if (passed) {
            return "Practice answer matched the expected weak-point answer at " + percent + "% overlap.";
        }
        return "Practice answer matched " + percent + "% of the expected answer; review the missing concepts and try again.";
    }

    private static Instant nextReviewAt(Instant now, double score, boolean passed) {
        if (passed) {
            return now.plus(score >= 0.85 ? 14 : 7, ChronoUnit.DAYS);
        }
        if (score >= 0.35) {
            return now.plus(1, ChronoUnit.DAYS);
        }
        return now.plus(4, ChronoUnit.HOURS);
    }

    public LearningWeakPointResponse toResponse(LearningWeakPoint weakPoint) {
        return new LearningWeakPointResponse(
                weakPoint.getId(),
                weakPoint.getSession().getId(),
                weakPoint.getKnowledgeBase() != null ? weakPoint.getKnowledgeBase().getId() : null,
                weakPoint.getEvidenceMessage() != null ? weakPoint.getEvidenceMessage().getId() : null,
                weakPoint.getTopic(),
                weakPoint.getExpectedAnswer(),
                weakPoint.getSourceHint(),
                weakPoint.getDifficulty(),
                weakPoint.getMasteryStatus(),
                weakPoint.getReviewCount(),
                weakPoint.getLastSeenAt(),
                weakPoint.getLastAssessedAt(),
                weakPoint.getPracticeCount(),
                weakPoint.getLastPracticeScore(),
                weakPoint.getNextReviewAt(),
                weakPoint.getCreatedAt()
        );
    }

    public record PracticeAssessmentResult(
            LearningWeakPointResponse updatedWeakPoint,
            WeakPointPracticeAssessmentResponse assessment
    ) {
    }

}
