# React Chat Citation Crash Review

## Scope

- Fixed the React chat page crash after a successful backend assistant turn.
- The crash happened when the citation side panel rendered `item.id.slice(...)` for raw backend citation objects that did not contain an `id` field.

## Review Focus

- Check `frontend-react/src/pages/ChatPage.tsx`.
- Verify historical assistant messages with raw `citations` JSON are normalized before rendering.
- Verify citation IDs fall back to `chunkId`, `chunk_id`, `documentId`, `document_id`, or a generated stable display ID.
- Verify missing title, location, snippet, score, page, or sheet fields do not break rendering.

## Validation

- `npm.cmd --prefix frontend-react run typecheck`
- `npm.cmd --prefix frontend-react run build`
