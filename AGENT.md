
# Development Guidelines

This file defines the working conventions for NFC Hub. Read `PROJECT.md` for the product scope and domain rules before changing the application.

## Working principles

- Make small, reviewable changes within the requested scope.
- Prefer explicit, maintainable code that a junior backend developer can explain.
- Inspect relevant files and Git status before editing.
- Preserve unrelated changes and avoid speculative features or broad refactors.
- Explain architectural decisions and their trade-offs before making significant changes.
- Do not hide errors or silently ignore failures.

## Project conventions

- The Python package is `src/nfc_hub`.
- Keep HTTP handling in `api/`, validation in `schemas/`, persistence entities in `models/`, and shared database, configuration and security code in `core/`.
- Put non-trivial business rules in services; introduce new directories only when needed.
- Manage schema changes with Alembic. Do not use `create_all()` in application code as a replacement for migrations.
- Use isolated databases in tests. Never modify the development database during automated tests.

## Language and documentation

- Write code, identifiers, comments, docstrings, commit messages and `CHANGELOG.md` in English.
- Write the README, release notes and future user-facing interface text in Spanish.
- Keep documentation aligned with implemented behavior; distinguish current features from plans.
- Add changes under `Unreleased` until preparing a release.
- Explain *why* in comments when the reason is not evident from the code.

## Git workflow

Use `main`, `develop` and short-lived branches such as `feature/*`, `bugfix/*` or `release/*`.

- Do not implement features directly on `main` or `develop`.
- Keep commits focused and use short English messages, such as `feat: add tag creation`.
- Do not rewrite history or discard user changes.
- Do not create branches, commit, merge, tag or push unless requested.

## Testing

- Run relevant tests after a change and the full suite when practical.
- Report the commands executed and their results.
- Add meaningful tests when behavior changes, including error and authorization cases.
- Keep tests deterministic and independent of external services.
- Do not remove or weaken tests to make the suite pass.

Main command:

```bash
python3 -m pytest -v
```

## Security and NFC rules

- Never store plaintext passwords or raw session tokens in the database.
- Enforce authentication and ownership on the server for every protected operation.
- Treat the NFC tag UID and public URL as readable and copyable; neither proves ownership.
- Generate public tag tokens with a cryptographically secure source. Tokens must be non-sequential and difficult to guess.
- Keep a tag's public URL stable when its destination changes.
- Scanning a tag must never authenticate its visitor or grant management access.
- Validate external destinations and avoid exposing sensitive data in public responses or logs.
- Use established security libraries rather than custom cryptography.
- Add rate limiting and deployment protections before exposing authentication publicly.

## Scope and dependencies

- The current application provides authentication; tag management and a frontend remain planned.
- Do not introduce a frontend framework, Docker, PostgreSQL or other substantial infrastructure without an explicit decision.
- Explain why a new dependency is needed before adding it.
- Keep the implementation consistent with the MVP and exclusions in `PROJECT.md`.

After completing a task, summarize the change, tests run and relevant limitations.