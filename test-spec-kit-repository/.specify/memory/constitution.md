<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0
Bump rationale: MINOR — Technology Stack section replaced with technology-agnostic
Project Scope section; title updated to remove language/framework specifics.

Modified principles: none

Modified sections:
  - "Simple Python API Constitution" → "Backend API Constitution"
  - Technology Stack → Project Scope (technology choices deferred to planning phase)

Removed sections: none

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check gates align with principles below
  ✅ .specify/templates/spec-template.md — No mandatory section changes required
  ✅ .specify/templates/tasks-template.md — Task categories align with principles below
  ✅ .specify/templates/constitution-template.md — Source template, no changes needed

Deferred TODOs:
  - TODO(TECHNOLOGY_STACK): Language, framework, test tooling, and linter to be decided
    during the first feature's planning phase and locked in plan.md Technical Context.
-->

# Backend API Constitution

## Core Principles

### I. API-First

Every feature MUST be exposed as an HTTP endpoint with a clearly defined request/response contract.
Endpoints MUST follow RESTful conventions (resource-based URLs, appropriate HTTP verbs, standard status codes).
Request and response bodies MUST use JSON.
Breaking changes to existing endpoints are NOT permitted without a version increment.

**Rationale**: The API surface is the product; contracts are commitments to callers and MUST be treated as such.

### II. Simplicity & YAGNI

Implementation MUST start with the simplest solution that satisfies the requirement.
No feature, abstraction, or dependency may be added unless it is required by a current, concrete user story.
Each endpoint MUST do one thing well; business logic MUST live in a service layer, not in route handlers.

**Rationale**: Premature complexity is the primary source of technical debt in small APIs. Enforce simplicity by default.

### III. Test-First (NON-NEGOTIABLE)

Tests MUST be written and confirmed failing before any implementation code is written (Red → Green → Refactor).
Every endpoint MUST have at least one integration test covering the happy path and one covering error paths.
Unit tests MUST cover all service-layer functions with non-trivial logic.

**Rationale**: Tests are the executable specification; writing them first prevents scope creep and guarantees coverage.

### IV. Explicit Error Handling

All error responses MUST return a JSON body with a `detail` field and an appropriate HTTP status code.
Unhandled exceptions MUST NOT leak stack traces or internal details to API consumers.
Input validation MUST occur at the API boundary and return HTTP 422 with field-level error details.

**Rationale**: Predictable error contracts are as important as the happy-path contract for API consumers.

### V. Observability

Every request MUST be logged with method, path, status code, and response time.
Application startup MUST log the runtime version, framework version, and bound host/port.
A `GET /health` endpoint MUST exist and return HTTP 200 with `{"status": "ok"}` when the service is healthy.

**Rationale**: Without minimal observability, production incidents cannot be diagnosed. These are the irreducible minimum.

## Project Scope

This is a backend HTTP API project. Technology choices (language, framework, test tooling, linter,
dependency manager) are intentionally deferred and MUST be decided and locked during the first
feature's planning phase in the `Technical Context` section of `plan.md`.

Constraints that apply regardless of technology choice:

- The API MUST be backend-only; no frontend or UI is in scope.
- No database or storage layer is assumed by default; storage decisions are feature-specific
  and MUST be justified in the plan's Complexity Tracking table.
- The chosen stack MUST support automated testing of HTTP endpoints.

## Development Workflow

- All work MUST be done on a feature branch; direct commits to `main` are NOT permitted.
- A pull request MUST pass all tests and linting before merge.
- Every merged change MUST include updated or new tests.
- Complexity exceptions (e.g., additional abstractions, new dependencies) MUST be documented in the plan's
  Complexity Tracking table with explicit justification.

## Governance

This constitution supersedes all other project practices and informal conventions.
Amendments MUST follow semantic versioning (MAJOR / MINOR / PATCH as defined in the spec-kit workflow),
be documented in the Sync Impact Report above, and be propagated to all dependent templates before merging.
All PRs and code reviews MUST verify compliance with the principles above before approval.
Violations require either a code fix or a documented complexity exception in the relevant plan.

**Version**: 1.1.0 | **Ratified**: 2026-03-25 | **Last Amended**: 2026-03-25
