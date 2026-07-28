
# AGENT.md

## Development Guidelines

This document defines how AI coding agents must work in the NFC Hub repository.

Before modifiying any file, read this document and `PROJECT.md` completely.

---

## Core Principles

- Work in small, reviewable increments.
- Implement only the requested scope.
- Prefer simple and maintainable solutions.
- Preserve the existing architechture and conventions.
- Do not introduce speculative features.
- Do not modify unrelated files.
- Do not hide errors or silently ignore failures.
- Explain important technical decisions clearly.
- Stop and ask before making an architectural change.

The project must remain understandable to a junior backend developer who may need to explain every implementation decision.

---

## Project Structure

The project uses a `src` layout.

```text
NFC_Hub/
├── src/
│   └── nfc_hub/
├── tests/
├── AGENT.md
├── PROJECT.md
├── README.md
├── CHANGELOG.md
└── requirements.txt

The root project directory may be named NFC_Hub, but the Python package must always use lowercase snake case:
src/nfc_hub/

As the application grows, prefer the following internal structure when required:

src/nfc_hub/
├── main.py
├── api/
├── core/
├── models/
├── schemas/
├── services/
├── templates/
└── static/
```

Do not create empty modules or directories before they are needed.

Keep responsibilities separated:

- API routes handle HTTP concerns.
- Service contain business logic.
- Models represent database entities.
- Schemas validate input and output data.
- Templates contain server-rendered HTML.
- Static files contain CSS, JavaScript and images.

---

## Language Style

Use:

- English for source code.
- English for identifiers.
- English for code comments.
- English for docstrings.
- English for commit messages.
- Spanish for user-facing interface text.
- Spanish for README documentation.
- English for CHANGELOG.
- Spanish for release notes.

Use clear and descriptive names.

Avoid unnecessary abbreviations and overly clever code.

---

## Documentation

Documentation is considered part of the project.

README:

- Written in Spanish.
- Explain the purpose of the project clearly.
- Keep installation and execution commands current.
- Include examples when they improve understanding.
- Do not document features that are not implemented.

CHANGELOG:

- Written in English.
- Follow Keep a Changelog.
- Follow Semantic Versioning.
- Add changes under the `Unreleased` section until a release is prepared.

Release Notes:

- Written in Spanish.
- Summarize user-facing changes.
- Avoid copying the CHANGELOG verbatin.

Code comments:

- Written in English.
- Explain why something is done, not what obvious code already does.

Docstrings:

- Written in English.
- Use them for public modules, classes and functions when they add useful context.

---

## Git Workflow

Use GitFlow.

Typical branches:

```text
main
develop
feature/*
bugfix/*
hotfix/*
release/*
```
Rules:

- Never work directly on `main`.
- Do not commit directly to `develop` when implementing a feature.
- Use short and descriptive branch names.
- Keep commits small and focused.
- Write commit messages in English.
- Do not create branches, commit, merge, tag or push unless explicitly requested.
- Do not rewrite Git history.
- Do not modify or discard existing user changes.

Preferred commit style:

```text
type: short description
```
Examples:

```text
chore: initialize project structure
docs: define project requirements
feat: add tag registration model
test: add tag ownership tests
fix: prevent unauthorized tag updates`
```

---

## Testing

Use `pytest`

Before considering a task finished:

- Run the relevant tests.
- Run the complete test suite when practical.
- Report the exact rest command used.
- Report whether tests passed or failed.
- Add or update tests when behavior changes.
- Test expected failures and authorization boundaries.
- Do not remove or weaken tests to makle the suite pass.
- Do not rely on external services in automated tests.
- Use isolated test data.
- Keep tests deterministic.

Security-sensitive functionality must include tests for:
- Unauthenticated access.
- Unauthorized access to another user's resources.
- Invalid or explired tokens.
- Inactive tags.
- Duplicate identifiers.
- Invalid input.

---

## Dependencies

- Prefer the Pythonstard library when it provides a clear solution.
- Add a dependency only when it provides meaningful value.
- Do not install or add dependencies without explaining why they are needed.
- Do not replace an existing dependency without approval.
- Avoid overlapping libraries that solve the same problem.
- Keep runtime and development dependencies identifiable.
- Never add a frontend framework without explicit approval.

When proposing a dependency, explain:

- What problem it solves.
- Why the standard library is insufficient.
- Its impact on maintenance and security.
- Wether a simpler alternative exists.

---

## APIs

The application uses FastAPI.

Rules:

- Keep route handlers small.
- Place business logic in services when it becomes non-trivial.
- Validate request and response data with Pydantic schemas.
- Use appropriate HTTP status codes.
- Return consistent and understandable errors.
- Do not expose internal database identifiers unnecessarily.
- Do not expose stack traces or sensitive implementatioan details.
- Keep public tag routes separte from authenticated management routes.
- Document endpoints through FastAPI where appropriate.

Public identifiers must be non-sequential and difficult to guess.

---

## Frontend

The initial frontend uses:

- Server-rendered templates with Jinja2.
- HTML.
- CSS.
- Minimal vanilla JavaScript.

Rules:

- Design mobile-first because NFC interactions primarly begin on phones.
- Keep the interface simple and accesible.
- Use semantic HTML.
- Provide clear validation and error messages.
- Do not introduce React, Vue, Angular, Node.js or a separate frontend build system without explicit approval.
- Do not place authorization or sensitive business rules exclusively in JavaScript.
- Treat all client-provided data as untrusted.

User-facing text must be written in Spanish.

---

## Database

Use SQLAlchemy for database access and Alembic for migrations when persistence is introduced.

Prefer:

- SQLite for initial local development.
- PostgreSQL for later deployment.

Rules:

- Keep database access separate from route handlers when practical.
- Use explicit relationships and constraints.
- Preserve data integrity at both application and database levels.
- Use migrations for schema changes.
- Do not use `create_all()` as a replacement for migrations once Alembic is configured.
- Do not modify existing migrations after they have been shared or released.
- Do not store plaintext passwords, activation codes or sensitive tokens.

---

## NFC Domain Rules

NFC Hub manages reusable NFC tags through permanent public URLs.

The NFC tag stores a URL similar to:

text```
https://example.com/t/<public_token>
```

The backend determines the current behavior associated with that token.

Important rules:

- The physical NFC tag and its assigned behavior are separate concepts.
- Reassigning a tag must not require rewriting the physical tag.
- NFC tag UIDs must no be treated as proof of identify or ownership.
- Public tag tokens must be generated with a cryptographically secure source.
- Public tokens must no be sequential.
- Scanning a tag must bever authenticate the visitor as its owner.
- Only the authenticated owner may manage a tag.
- Ownership transfers require an explicit and secure process.
- A copied public URL must no grant management access.
- Do not rely on NFC hardware write protection as the application's primary security mechanism.

The initial hardware target is:

```text
NTAG215
NFC Forum Type 2
504 bytes of usable memory
NDEF URL record
```

Maintain compatibility with Android and IPhone NFC readers.

---

## Security

Security must be implemented without creating unnecessary friction for users.

Rules:

- Follow established authentication and session-management practices.
- Hash passwords using a suitable password-hashing library.
- Never store or log plaintext passwords.
- Never store sensitive tokens in plaintext when a hashed representation is sufficient.
- Use secure, random and expiring tokens where appropriate.
- Enforce authorization on the server for every protected operation.
- Never trust ownership identifiers received from the client.
- Prevent users from accessing or modifying another user's tag.
- Keep secrets in environment variable.
- Never commit credentials, API keys or local environment files.
- Avoid exposing personal contact data on public tag pages.
- Rate-limit sensitive or abuse-prone operations when required.
- Require additional confirmation only for sensitive actions such as account changes, tag transfers or account deletion.

Do not implement custom cryptography.

---

## Docker

Docker is not required for the first development increments.

When Docker is introduced:

- Keep the configuration minimal.
- Use official base images.
- Do not store secrets in images or Compose files.
- Add health checks where they provide operational value.
- Keep development and production concerns clearly separated.
- Document all required commands.

Do not introduce Docker before it is requested.

---

## Documentation Quality

When modifying documentation:

- Keep examples updated.
- Keep version numbers consistent.
- Update `CHANGELOG.md` when needed.
- Update `README.md` if features, commands or setup steps change.
- Prefer clear explanations over overly technical wording.
- Distinguish implemented features from planned features.
- Do not claim that a security property exists unless it is actually enforced and tested.

---

## Agent Behaviour

Before editing code:

1. Read `AGENT.md` and `PROJECT.md`.
2. Inspect the relevant existing files.
3. Check the current Git status.
4. Summarize the intended change.
5. Identify any ambiguity or architectural impact.

When editing code:

- Make the smallest coherent change.
- Preserve existing behavior unless the task requres changing it.
- Do not perform broad refactors alongside a feature.
- Do not reformat unrelated code.
- Do not generate large amounts of boilerplate without justification.
- Add comments only when they provide useful context.
- Verify imports, execution and tests.

If multiple solutions exist:

- Present the simplest suitable option first.
- Explain the relevant trade-offs.
- Do not implement an alternative until a decision has been made.

If an improvement could be beneficial but was not requested:

- Mention it as a possible follow-up
- Do not implement it automatically.

After completing a task:

1. Summarize what changed.
2. List the files modified.
3. Report the tests or checks executed.
4. Mention remaining limitations or follow-up work.
5. Stop and wait for the next instruction.

Never introduce unnecessary complexity.

---

## Philosophy

NHF Hun should grow through small, understandable and tested increments.

The objective is not only produce working software, but to maintain a codebase whose architecture, security decisions and behavior
can be clearly explained and defended.
