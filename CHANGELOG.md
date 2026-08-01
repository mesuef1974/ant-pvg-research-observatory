# Changelog

All notable changes are recorded here. The project is pre-release and follows semantic-versioning intent.

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
