# Frontend Workbench Wiring

Date: 2026-06-08

## Scope

- Keep frontend responsibility limited to Vue UI, API client behavior, and store state mapping.
- Continue routing API calls through Spring Boot `/api/*`; do not call FastAPI directly from the browser.
- Close the high-priority workbench gaps found during multi-agent review.

## Completed

- Runtime Settings now drive the frontend API client for `apiBaseUrl`, request timeout, and trace header inclusion.
- Persisted Settings are loaded back into the Settings page and shared with the API client through one storage key.
- Chat session history records are mapped into visible thread messages, including persisted citations when available.
- Knowledge base page now supports create, detail refresh, edit, and delete actions.
- Documents page now supports detail inspection, chunk display, parser/source metadata display, and delete actions.
- Upload form now validates target knowledge base, title, file name/content, allowed extensions, and a 10 MB file size limit before submit.

## Verification

- `npm.cmd run typecheck`
- `npm.cmd run build`
