# Changelog

All notable changes are recorded here. The project is pre-release and follows semantic-versioning intent.

## [0.2.0-dev] — 2026-08-02

### Added

- Governed local PDF import from paths inside `library/`.
- Multi-document registry API.
- SHA-256 deduplication.
- PDF page-count and file-size metadata.
- Explicit source-layer assignment for every imported document.
- Path-containment and PDF-type validation.
- Compatibility upgrade for v0.1 SQLite document tables.
- Tests for PDF import and duplicate detection.

### Governance

- Imported files remain local and are referenced by relative path only.
- A document cannot escape the configured library root.
- Reimporting identical bytes does not create a second record.

## [0.1.0-dev] — 2026-08-02

### Added

- Governed repository foundation on `agent/platform-v1-foundation`.
- Local-first data exclusion policy.
- Python package configuration for FastAPI, SQLAlchemy, Alembic, and PyPDF.
- Typed runtime settings.
- Initial database entities for documents, claims, source layers, and literature gates.
- Health and source-governance API endpoints.
- Test suite and GitHub Actions CI.
- Initial platform roadmap and Windows local setup instructions.

### Governance

- The three source layers are stored and judged separately.
- Model synthesis cannot certify an external fact or a novelty claim.
- `NOT-FOUND-YET` is not equivalent to `NOVEL`.
- PDFs, secrets, and operational databases are not committed.
