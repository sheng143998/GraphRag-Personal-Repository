# 2026-06-15 Experiment Workflow Humanization

## Goal

把实验评估页改造成更人性化的工作流入口：在实验页内直接运行 RAG、导入评测集、保存样本、再批量评估，不再要求用户先理解 run / sample / case 的内部关系。

## Scope

- 前端实验页增加“直接运行 RAG”区域。
- 前端实验页增加“导入评测集”区域，支持 JSON / CSV 粘贴或文件导入。
- 后端补齐评测集导入接口，按 `experimentId + caseId` 幂等导入。
- 保留原有单样本编辑、批量评估和历史回看。

## Files

- `frontend/src/pages/experiments/ExperimentsPage.vue`
- `frontend/src/api/experiments.ts`
- `frontend/src/api/rag.ts`
- `frontend/src/types/index.ts`
- `backend-java/src/main/java/com/example/agentknowledge/controller/RagController.java`
- `backend-java/src/main/java/com/example/agentknowledge/service/RagExperimentService.java`
- `backend-java/src/main/java/com/example/agentknowledge/repository/RagEvaluationCaseRepository.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/ImportRagEvaluationCasesRequest.java`
- `backend-java/src/main/java/com/example/agentknowledge/dto/rag/ImportRagEvaluationCasesResponse.java`

## Validation

- `npm.cmd --prefix frontend run typecheck`
- `mvn.cmd -f backend-java/pom.xml -q -DskipTests compile`
- 浏览器验证 `/experiments` 页面是否能直接运行 RAG、导入评测集、生成样本。
