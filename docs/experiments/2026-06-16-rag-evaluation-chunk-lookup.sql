-- RAG 评测集 chunk 证据查询 SQL
--
-- 使用方式：
-- 1. 先将 datasets/processed/rag-folder-evaluation-cases-20260616.json 导入某个实验。
-- 2. 将下面 SQL 中的 experiment_id 占位 UUID 替换为你的实验 UUID。
-- 3. 运行查询 1 检查 relevantChunkIds / expectedCitationChunkIds 对应的真实 chunk 内容。
-- 4. 如只想查某个样例，可在 target_cases CTE 里追加：
--    AND ec.case_id = 'rag-basic-offline-online-flow'

-- 查询 1：展开 relevantChunkIds 和 expectedCitationChunkIds，并查看对应 chunk 正文。
WITH target_cases AS (
    SELECT
        ec.id,
        ec.experiment_id,
        ec.case_id,
        ec.question,
        ec.expected_answer,
        ec.relevant_chunk_ids,
        ec.expected_citation_chunk_ids
    FROM rag_evaluation_cases ec
    WHERE ec.experiment_id = '00000000-0000-0000-0000-000000000000'::uuid
),
expanded_targets AS (
    SELECT
        tc.case_id,
        tc.question,
        'relevant' AS target_kind,
        value::uuid AS chunk_id
    FROM target_cases tc
    CROSS JOIN LATERAL jsonb_array_elements_text(tc.relevant_chunk_ids) AS value
    UNION ALL
    SELECT
        tc.case_id,
        tc.question,
        'expected_citation' AS target_kind,
        value::uuid AS chunk_id
    FROM target_cases tc
    CROSS JOIN LATERAL jsonb_array_elements_text(tc.expected_citation_chunk_ids) AS value
)
SELECT
    et.case_id,
    et.target_kind,
    et.chunk_id,
    d.id AS document_id,
    d.title AS document_title,
    d.file_name,
    c.chunk_index,
    c.title AS chunk_title,
    c.chunk_strategy,
    LEFT(REGEXP_REPLACE(c.content, E'[\\n\\r\\t]+', ' ', 'g'), 1200) AS content_preview
FROM expanded_targets et
LEFT JOIN document_chunks c ON c.id = et.chunk_id
LEFT JOIN documents d ON d.id = c.document_id
ORDER BY et.case_id, et.target_kind, c.chunk_index, et.chunk_id;


-- 查询 2：检查评测集中是否存在无效 chunkId。
WITH target_cases AS (
    SELECT *
    FROM rag_evaluation_cases ec
    WHERE ec.experiment_id = '00000000-0000-0000-0000-000000000000'::uuid
),
expanded_targets AS (
    SELECT ec.case_id, 'relevant' AS target_kind, value::uuid AS chunk_id
    FROM target_cases ec
    CROSS JOIN LATERAL jsonb_array_elements_text(ec.relevant_chunk_ids) AS value
    UNION ALL
    SELECT ec.case_id, 'expected_citation' AS target_kind, value::uuid AS chunk_id
    FROM target_cases ec
    CROSS JOIN LATERAL jsonb_array_elements_text(ec.expected_citation_chunk_ids) AS value
)
SELECT et.*
FROM expanded_targets et
LEFT JOIN document_chunks c ON c.id = et.chunk_id
WHERE c.id IS NULL
ORDER BY et.case_id, et.target_kind;


-- 查询 3：按样例汇总 relevant / expected_citation 数量。
SELECT
    ec.case_id,
    jsonb_array_length(ec.relevant_chunk_ids) AS relevant_chunk_count,
    jsonb_array_length(ec.expected_citation_chunk_ids) AS expected_citation_chunk_count,
    ec.evaluation_top_k,
    ec.status
FROM rag_evaluation_cases ec
WHERE ec.experiment_id = '00000000-0000-0000-0000-000000000000'::uuid
ORDER BY ec.case_id;


-- 查询 4：查看某次 RAG run 的召回结果是否命中 expectedCitationChunkIds。
-- 将 run_id 替换为某次 RAG run UUID。
WITH target_cases AS (
    SELECT *
    FROM rag_evaluation_cases ec
    WHERE ec.experiment_id = '00000000-0000-0000-0000-000000000000'::uuid
),
expected_targets AS (
    SELECT ec.case_id, value::uuid AS chunk_id
    FROM target_cases ec
    CROSS JOIN LATERAL jsonb_array_elements_text(ec.expected_citation_chunk_ids) AS value
)
SELECT
    rr.run_id,
    rt.case_id,
    rr.rank,
    rr.chunk_id,
    rr.document_id,
    rr.score,
    CASE WHEN et.chunk_id IS NULL THEN false ELSE true END AS hit_expected_citation,
    d.title AS document_title,
    c.title AS chunk_title,
    LEFT(REGEXP_REPLACE(c.content, E'[\\n\\r\\t]+', ' ', 'g'), 800) AS content_preview
FROM rag_retrieval_results rr
JOIN rag_runs r ON r.id = rr.run_id
JOIN target_cases rt ON rt.question = r.question
LEFT JOIN expected_targets et ON et.case_id = rt.case_id AND et.chunk_id = rr.chunk_id
LEFT JOIN document_chunks c ON c.id = rr.chunk_id
LEFT JOIN documents d ON d.id = rr.document_id
WHERE rr.run_id = '00000000-0000-0000-0000-000000000000'::uuid
ORDER BY rt.case_id, rr.rank;
