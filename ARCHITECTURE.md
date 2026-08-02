# ANT–PVG Research Observatory — Architecture

## 1. Mission

The observatory is a local-first research platform for analytic number theory and Prime-Valuation Geometry. It separates evidence, synthesis, and research claims so that search and automation cannot silently turn an unsupported idea into a certified result.

## 2. Authoritative source layers

Every evidence-bearing object belongs to exactly one source layer:

- `ENCYCLOPEDIA`: internally curated material from the governed encyclopedia corpus.
- `LITERATURE`: externally published material with traceable bibliographic evidence and reading status.
- `MODEL_SYNTHESIS`: generated explanations, proposed links, conjectures, and search leads. This layer cannot certify an external fact or novelty claim.

Source layers are classifications, not confidence scores. A claim may cite evidence from several layers, but the evidence items remain separate.

## 3. Core domain objects

```text
Document
  └── DocumentPage
        └── EvidenceSpan          (planned)
              └── ClaimEvidence  (planned)

Claim
  ├── ClaimDependency            (planned)
  ├── LiteratureMatch            (planned)
  └── LiteratureGate

Reference                        (planned)
KnowledgeNode / KnowledgeEdge    (planned)
Experiment / Artifact            (planned)
```

### Document

A local file registered by SHA-256 and a path relative to the configured library root. Files remain outside Git.

### DocumentPage

The smallest first-class retrieval unit in phase 3. It stores one PDF page's extracted text, counts, extraction status, and a text hash. Page numbering is one-based and unique within a document.

### Claim

A governed mathematical statement with a status, source layer, evidence, novelty note, and dependencies. `NOT-FOUND-YET` is never equivalent to `NOVEL`.

### LiteratureGate

A bounded review process attached to a specific research question. A gate records search scope, matched literature, unresolved differences, and a verdict.

## 4. Data flow

```text
Local PDF
  → path-containment validation
  → SHA-256 registration
  → PDF metadata
  → per-page extraction
  → Unicode normalization
  → page hashes and counts
  → text search
  → evidence spans
  → claims and literature gates
  → knowledge graph
```

No later stage may overwrite the raw extraction silently. Normalized or enriched representations must remain reproducible from the registered source file and extraction version.

## 5. Storage boundaries

### Git-tracked

- application code;
- database migrations;
- tests;
- schemas and governance documents;
- reproducible scripts.

### Local-only

- PDFs and books under `library/`;
- operational SQLite databases under `data/`;
- search indexes and caches;
- secrets and environment files;
- generated exports unless explicitly curated.

## 6. Database migration policy

- Alembic is the sole schema-version authority.
- Production-like local databases are upgraded, not deleted.
- Migrations that touch inherited MVP data must include a regression test.
- Destructive downgrades are not fabricated when reconstruction would invent data.
- Runtime startup may create directories but must not perform undocumented schema mutations.

## 7. Retrieval policy

Phase 3 begins with page-level retrieval:

1. exact page storage;
2. deterministic re-indexing;
3. plain full-text search;
4. evidence citations by document and page;
5. later semantic retrieval as an additional index, never as the sole evidence store.

Search results must always preserve:

- document identity;
- source layer;
- one-based page number;
- the matched text or bounded snippet;
- extraction status.

## 8. Extraction statuses

```text
PENDING
EXTRACTED
EMPTY
PARTIAL
FAILED
```

`EMPTY` means the extraction engine returned no non-whitespace text. It does not prove that the visual PDF page is blank. OCR or visual inspection is a later explicit workflow.

## 9. Re-indexing invariants

For a document with unchanged SHA-256:

- indexing is idempotent;
- `(document_id, page_number)` is unique;
- a complete re-index replaces stale page rows atomically;
- page count in the document registry must equal the number of indexed page rows after a successful full indexing run;
- extraction failures are recorded, not hidden.

## 10. API boundaries for phase 3

```text
POST /api/documents/{document_id}/index-pages
GET  /api/documents/{document_id}/pages
GET  /api/search/pages?q=...
```

The first phase-3 delivery implements indexing and page listing. Search follows after the extraction schema and idempotency tests pass.

## 11. Planned phases

### P3 — Page indexing and exact search

- `document_pages` schema;
- PDF text extraction page by page;
- deterministic re-indexing;
- page-list API;
- exact full-text search;
- evidence-location foundation.

### P4 — Claims and evidence

- evidence spans;
- claim-to-page links;
- claim status workflows;
- contradiction and equivalence records.

### P5 — Literature observatory

- references, DOI/BibTeX ingestion, reading status;
- literature-gate matrices;
- citation graph and duplicate resolution.

### P6 — Knowledge graph and PVG laboratory

- theorem, method, object, and dependency nodes;
- PVG/PVFC computations and experiment artifacts;
- links between computations, claims, and literature evidence.

## 12. Non-goals

The platform does not:

- certify novelty from absence of a search result;
- treat model-generated text as external evidence;
- commit copyrighted PDFs to Git;
- silently OCR or alter mathematical text;
- replace specialist review with similarity search.
