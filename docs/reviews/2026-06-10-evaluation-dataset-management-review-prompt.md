# 2026-06-10 Evaluation Dataset Management Review Prompt

## Review Goal

Please review the evaluation dataset management refactor. Verify that the experiment page is now a persistent evaluation-set tool instead of a one-off run evaluator, and that the backend still keeps scoring logic inside FastAPI while Spring Boot only persists business data and bridges requests.

## Key Files

- `backend-java/src/main/java/com/example/agentknowledge/domain/RagEvaluationCase.java`
- `backend-java/src/main/java/com/example/agentknowledge/repository/RagEvaluationCaseRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/CreateRagEvaluationCaseRequest.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/UpdateRagEvaluationCaseRequest.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/RagEvaluationCaseResponse.java`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/resources/db/migration/V202606101510__create_rag_evaluation_cases.sql`
- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/api/experiments.ts`
- `frontend/src/types/index.ts`
- `frontend/src/styles.css`

## Review Focus

1. Does the new `rag_evaluation_cases` model cover question, expected answer, relevant chunk/document labels, expected citation labels, `topK`, notes, and status?
2. Does Spring Boot keep the evaluator bridge to FastAPI instead of moving scoring logic into Java?
3. Is the frontend page usable as a management tool for datasets/cases, and not just a score summary page?
4. Are the new endpoints consistent with the existing `/api/rag/*` convention?
5. Do the new UI states preserve the existing workbench style and responsive constraints?

## Validation

- `mvn -f backend-java/pom.xml test`
- `npm.cmd --prefix frontend run typecheck`
- `npm.cmd --prefix frontend run build`
- Preview the `/experiments` page in browser and check layout on desktop and mobile.
