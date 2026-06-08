from app.services.adapters.openai_compatible import _extract_embeddings, _extract_rerank_scores


def test_extract_embeddings_sorts_by_index():
    data = {
        "data": [
            {"index": 1, "embedding": [0.3, 0.4]},
            {"index": 0, "embedding": [0.1, 0.2]},
        ]
    }

    assert _extract_embeddings(data) == [[0.1, 0.2], [0.3, 0.4]]


def test_extract_rerank_scores_restores_original_document_order():
    data = {
        "results": [
            {"index": 1, "relevance_score": 0.2},
            {"index": 0, "relevance_score": 0.9},
        ]
    }

    assert _extract_rerank_scores(data, document_count=2) == [0.9, 0.2]


def test_extract_rerank_scores_supports_output_results_shape():
    data = {
        "output": {
            "results": [
                {"index": 0, "score": 0.7},
                {"index": 2, "score": 0.3},
            ]
        }
    }

    assert _extract_rerank_scores(data, document_count=3) == [0.7, 0.0, 0.3]


def test_extract_rerank_scores_pads_direct_score_list():
    assert _extract_rerank_scores({"scores": [0.5]}, document_count=3) == [0.5, 0.0, 0.0]