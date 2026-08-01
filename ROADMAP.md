# Roadmap

## Phase 0 — Platform foundation

- [x] Initialize governed repository.
- [x] Separate the three source layers.
- [x] Define initial claim and literature-gate entities.
- [x] Add FastAPI health/governance endpoints.
- [x] Add tests, linting, and CI.
- [ ] Add Alembic migrations.
- [ ] Add document/reference/evidence schemas.
- [ ] Add multi-document local library importer.

## Phase 1 — Research corpus

- Import multiple PDFs with hashes and provenance.
- Preserve page-level citations and extraction diagnostics.
- Add BibTeX/DOI ingestion and reading-status workflow.
- Link claims to evidence spans and references.

## Phase 2 — Literature gates

- Search-query ledger and synonym sets.
- Paper comparison matrix.
- `KNOWN / EQUIVALENT / PARTIAL / NOT-FOUND-YET` verdicts.
- Gate closure reports with explicit uncertainty.

## Phase 3 — ANT/PVG knowledge graph

- Concepts, theorems, methods, dependencies, and equivalences.
- Encyclopedia chapter links.
- PVG/PVFC research-path links.
- Graph exploration and export.

## Phase 4 — Scientific workbench

- Dirichlet-series and symmetric-function tools.
- Reproducible numerical experiments.
- Claim-to-computation evidence links.
- Governance checks preventing unsupported novelty claims.
