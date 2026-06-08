# Review Prompt: GraphRAG Offline Evaluation Fixture

Review the fixture for these concerns:

- The graph cases use explicit relevant chunk ids and expected citation ids rather than relying on fragile text matching.
- `graph-rag` wins because it retrieves relationship/traversal evidence, not because the test hardcodes a meaningless label.
- The fixture remains offline and deterministic.
- No browser or Spring Boot boundary is changed by this AI-service-only test addition.
