from app.schemas.rag import RagEvaluateRequest, RagEvaluationResult


class BaseRagEvaluator:
    async def evaluate(self, payload: RagEvaluateRequest) -> RagEvaluationResult:
        raise NotImplementedError


class SimpleRagEvaluator(BaseRagEvaluator):
    async def evaluate(self, payload: RagEvaluateRequest) -> RagEvaluationResult:
        grounded_score = 1.0 if payload.citations else 0.2
        retrieval_score = min(1.0, len(payload.citations) / 5) if payload.citations else 0.0
        notes = [
            "Skeleton evaluator uses simple heuristic scoring.",
            "Replace with adapter-backed or dataset-backed evaluation later.",
        ]
        return RagEvaluationResult(
            grounded_score=grounded_score,
            retrieval_score=retrieval_score,
            notes=notes,
        )
