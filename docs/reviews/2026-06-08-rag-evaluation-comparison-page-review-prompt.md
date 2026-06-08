# Review Prompt: RAG Evaluation Comparison Page

Review the new frontend comparison page for these concerns:

- Browser data access still goes through Spring Boot `/api/*` via existing frontend API/store abstractions.
- Aggregation logic handles missing scores, missing run context, and empty evaluation history.
- Layout remains readable on desktop and mobile without overlapping text.
- Existing experiment CRUD/evaluation flows are unchanged.
