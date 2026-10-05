# ADR-0002: One repository with uv, pnpm, and just

- **Status:** Accepted
- **Date:** 2026-09-22
- **Backfilled:** yes
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

Back-end, front-end, and end-to-end tests live in one repository driven by uv
(Python), pnpm (JS), and just (tasks), with one CI pipeline.

## Context

A feature routinely changes the API shape, the client that consumes it, and the
tests that prove it. Splitting those across repositories turns every such change
into coordinated pull requests and version chasing. The project also needs one
set of git hooks and one CI entry point.

## Decision

- One repository: `back-end/`, `front-end/`, `e2e/`, `documentation/`.
- Package management: `uv` for Python, `pnpm` for JavaScript.
- Task runner: `just` exposes the common commands (`just back-end`,
  `just test-back-end`, `just lint`, …) so the two toolchains share one entry
  point.
- Hooks: Husky + commitlint (Conventional Commits) + lint-staged.
- CI: one GitHub Actions workflow with back-end (ruff, pytest), front-end
  (eslint, prettier, vitest, build), and gitleaks jobs.

## Consequences

- **Easier:** cross-stack changes land atomically in one commit and one CI run.
- **Harder:** contributors need both toolchains installed; two lockfiles to
  keep current.
- **We now live with:** `just` is the documented interface; running raw tool
  commands risks drifting from it.

## Alternatives considered

- **Separate repositories** — cross-stack changes become coordinated PRs.
- **No task runner** — commands diverge between docs, CI, and local shells.
- **Lefthook instead of Husky** — used in a sibling project; deliberately
  varying the toolchain here.
