# Review Prompt: Structured RAG Evaluation UI

Review the structured evaluation UI for these concerns:

- The frontend still calls only Spring Boot `/api/*` endpoints.
- Structured evaluation case ids are generated from selected persisted run details, not manually guessed.
- Users can clear the structured case and fall back to the simple expected-answer flow.
- The evaluate action submits optional structured fields only when a case has been selected.
- Typecheck/build and full-chain smoke still pass.
