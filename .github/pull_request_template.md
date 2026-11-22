<!-- One change per pull request. If it cannot be reviewed in one sitting, split it. -->

## What changes

<!-- What is different after this merges? Two or three sentences. -->

## Why

<!-- The problem, or the requirement this serves. Reference the issue and any FR identifier. -->

Closes #

## Decision record

<!-- A change that is hard to reverse needs an ADR. Delete this section if it does not. -->

- [ ] ADR added to `docs/architectural-decision-records/`
- [ ] Not a decision — no ADR needed

## Migrations

<!-- Delete if the change carries no schema change. -->

- [ ] None
- [ ] Additive only — safe to deploy before the code
- [ ] Requires the code first — deploy order is described below

Deploy order:

## Evidence

<!-- What was run, and what was seen. "Tests pass" is not evidence on its own. -->

- [ ] `just test-backend`
- [ ] `just test-frontend`
- [ ] `just test-e2e`
- [ ] `just lint`
- [ ] Exercised manually: <!-- which flow, and what you observed -->

## Checklist

- [ ] Feature boundaries respected — no import of another feature's internals
- [ ] Public API of a feature updated in its `__init__.py` or `index.ts`
- [ ] Tests added or adjusted at the layer that changed
- [ ] Documentation updated if behaviour or setup changed
- [ ] No secrets, keys or personal data in the diff
