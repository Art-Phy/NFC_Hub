
## PROJECT.md

### Project Context

This document describes the purpose, current status and technical context of NFC Hub.

It is intended to help developers and AI agents understand the project before making changes.

Before modifying the repository, read this document and `AGENT.md` completely.

---

### Overview

NFC Hub is a web application for managing reusable NFC tags.

Each physical tag stores a permanent public URL. The owner can change the content or action associated with that URL through the application without rewriting the NFC tag.

A tag may initially redirect to a configurable external URL. Future versions may support additional content types and actions.

Example stored on the NFC tag:

```text
https://example.com/t/8QK4M7PX
```

When the tag is scanned, NFC Hub resolves the public token and performs the currently configured behavior.

The project combines:

- Backend development with FastAPI.
- Persistent data management.
- Authentication and authorization.
- A lightweight server-rendered frontend.
- NFC hardware testing.
- Security-focused ownership rules.
- Automated testing.

---

### Goal

The main goal is to create a simple and secure platform where users can:

1. Create an account and authenticate.
2. Register an NFC tag in their account.
3. Associate the tag with a configurable destination.
4. Write the permanent public URL to a physical NFC tag.
5. Scan the tag from Android or iPhone.
6. Change its destination later without rewriting it.
7. Activate or deactivate the tag.
8. Manage only the tags they own.

The project must demonstrate a clear separation between:

- The physical NFC tag.
- The permanent public URL stored on it.
- The authenticated owner.
- The configurable behavior resolved by the backend.

Scanning or copying a public NFC URL must never grant management access or prove ownership.

---

### MVP Scope

The first usable version should include:

- FastAPI application.
- Server-rendered interface using Jinja2.
- User registration.
- User authentication and logout.
- Secure password hashing.
- Authenticated tag management.
- Creation of a tag with a secure public token.
- Configurable external URL destination.
- Public tag resolution endpoint.
- Tag activation and deactivation.
- Ownership and authorization validation.
- Persistent storage using SQLAlchemy.
- Database migrations using Alembic.
- Automated tests using pytest.
- Clear instructions for writing the generated URL to an NTAG215 tag.

The initial behavior will be:

```text
Redirect to an external HTTPS URL
```

The MVP does not require direct NFC writing from the web application. During the initial development phase, tags will be written using a Flipper Zero with Momentum firmware.

---

### Out of Scope for the Initial Version

The following features must not be implemented unless explicitly requested:

- Native Android or iOS applications.
- Direct NFC writing from the browser.
- React, Vue, Angular or another frontend framework.
- A separate frontend application.
- Social login.
- Email verification.
- Password recovery by email.
- Ownership transfer.
- Team or organization accounts.
- Paid plans or subscriptions.
- QR code generation.
- Advanced analytics.
- Geolocation tracking.
- Webhooks.
- Custom domains.
- Multiple actions per tag.
- Contact cards or file hosting.
- Public user profiles.
- Docker deployment.
- PostgreSQL deployment.
- Background task queues.
- Redis.
- Microservices.
- Hardware UID authentication.
- Custom cryptography.

These may be evaluated in later versions after the core workflow is stable and tested.

---

### Current Status

Current project status:

```text
Early development
```

Current version:

```text
v0.4.0
```

Current branch:

```text
develop
```

The repository currently contains:

- Initial project structure.
- Minimal FastAPI application in `src/nfc_hub`.
- Health endpoint available at `GET /health`.
- Project packaging configuration in `pyproject.toml`.
- Editable installation support for the `src` layout.
- Separate runtime and testing dependency groups.
- Centralized pytest configuration.
- Centralized application settings through `AppSettings`.
- Environment-variable support using the `NFC_HUB_` prefix.
- Configurable application name, environment and debug mode.
- Automatic version resolution from installed package metadata.
- Configurable database URL.
- Database infrastructure using SQLAlchemy 2.x.
- SQLite as the default database for local development.
- SQLAlchemy engine and session factory.
- Declarative base prepared for future models.
- Alembic configuration prepared for database migrations.
- Automated tests using pytest and FastAPI's test client.
- AI development guidelines.
- Detailed project definition.
- User documentation.
- Physical NTAG215 writing, rewriting and scanning validation.

The project can be installed in editable mode using `requirements.txt`.

The `nfc_hub` package can be imported and the complete test suite can be executed without manually configuring `PYTHONPATH`.

The FastAPI application currently uses centralized settings for:

- Application title.
- Application version.
- Debug mode.

The application settings are defined in:

```text
src/nfc_hub/core/settings.py
```

The following environment variables are currently supported:

```bash
NFC_HUB_APP_NAME
NFC_HUB_ENVIRONMENT
NFC_HUB_DEBUG
NFC_HUB_DATABASE_URL
```

The default database URL is:

```text
sqlite:///./nfc_hub.db
```

The database infrastructure is defined in:

```text
src/nfc_hub/core/database.py
```

The application, editable installation, package import, health endpoint, database infrastructure and Alembic configuration have been validated successfully.

The current test suite contains 20 passing tests.

No NFC Hub business functionality has been implemented yet. Authentication, user persistence, tag persistence, tag management and public tag resolution remain planned.

No application tables or Alembic migration revisions exist yet.

---

### Tech Stack

Backend:

- Python 3.10 or later.
- FastAPI.
- Uvicorn.
- Pydantic.
- Pydantic Settings.

Frontend:

- Jinja2.
- HTML.
- CSS.
- Minimal vanilla JavaScript.

Persistence:

- SQLAlchemy 2.x.
- Alembic.
- SQLite for local development.

Planned for a later deployment phase:

- PostgreSQL.

Testing:

- pytest.
- FastAPI test client or HTTPX, depending on the application setup.

Hardware and NFC:

- NTAG215 tags.
- NFC Forum Type 2.
- 504 bytes of usable memory.
- NDEF records.
- Flipper Zero.
- Momentum firmware.
- NFC Maker.
- Android NFC reader.
- iPhone NFC reader.

Tags are initially written using NFC Maker on the Flipper Zero.

---

### Domain Model

The initial domain is expected to include the following concepts.

#### User

Represents an authenticated account that can own and manage NFC tags.

Expected responsibilities:

- Store account identification data.
- Store a securely hashed password.
- Own zero or more tags.
- Authenticate before accessing management operations.

#### Tag

Represents a logical NFC tag managed by the application.

Expected responsibilities:

- Belong to exactly one user.
- Have a secure public token.
- Store its current destination.
- Indicate whether it is active.
- Record creation and update timestamps.

The public token must:

- Be generated using a cryptographically secure source.
- Be non-sequential.
- Be difficult to guess.
- Not expose the database identifier.
- Remain stable when the destination changes.

#### Tag Destination

For the initial version, the destination is an external HTTPS URL.

The exact database representation must remain simple. A separate destination model is not required while each tag supports only one URL behavior.

A more generic action or destination system may be introduced later if multiple tag behaviors are implemented.

#### Scan Event

Scan analytics are not required for the first increment.

A scan event model may be introduced in a later version to record limited, privacy-conscious analytics. It must not be created speculatively before analytics are requested.

---

### Core Workflow

The intended user workflow is:

1. A user creates an account.
2. The user signs in.
3. The user creates a logical tag in NFC Hub.
4. NFC Hub generates a permanent public URL.
5. The user writes that URL to an NTAG215 tag using the Flipper Zero.
6. A phone scans the physical tag.
7. The public endpoint resolves its token.
8. NFC Hub redirects the visitor to the configured destination.
9. The owner changes the destination from the management interface.
10. The same physical NFC tag now resolves to the new destination without being rewritten.

If a tag is inactive or the token does not exist, the application must show an understandable public error page and must not reveal internal information.

---

### Public URL Design

The expected public route format is:

```text
/t/{public_token}
```

Example:

```text
https://example.com/t/8QK4M7PX
```

The final token format and length must be chosen before implementing tag creation.

Requirements:

- Cryptographically secure generation.
- Sufficient entropy to resist guessing.
- URL-safe characters.
- Unique database constraint.
- No sequential values.
- No user ID or database ID exposure.

The public route must not:

- Authenticate the visitor.
- Reveal the owner.
- Expose internal identifiers.
- Allow the destination to be modified.
- Grant access to management functionality.

---

### Security Model

The security model is based on authenticated accounts and server-side authorization.

Important assumptions:

- NFC tag content can be read and copied.
- A public NFC URL is not secret.
- The tag UID may be readable or reproducible.
- Physical write protection is not a substitute for application security.
- Anyone with the URL may visit the public destination.
- Only the authenticated owner may manage the tag.

Every protected tag operation must verify ownership on the server.

The application must protect against:

- Unauthorized access to another user's tags.
- Modification of another user's tags.
- Predictable public identifiers.
- Duplicate public tokens.
- Invalid destination URLs.
- Open redirects outside the intended tag resolution behavior.
- Plaintext password storage.
- Session or authentication data exposure.
- Sensitive information in logs or public errors.

The authentication mechanism must be selected and documented before implementation. The initial application should prefer a conventional server-side approach suitable for a server-rendered web interface.

Do not implement authentication until the chosen session strategy, password hashing library and CSRF requirements have been reviewed.

---

### NFC Compatibility

The initial physical tags are:

```text
NTAG215
NFC Forum Type 2
504 bytes of usable memory
NDEF formatted
```

The tag will store only the permanent NFC Hub URL during the normal application workflow.

The application must keep public URLs short enough to fit comfortably in the available tag memory.

Validated laboratory workflow:

1. Read a blank NTAG215 using the Flipper Zero.
2. Create an NDEF record using NFC Maker.
3. Write the record to the NTAG215.
4. Read the physical tag again to verify its contents.
5. Scan the tag successfully using Android.
6. Scan the tag successfully using iPhone.
7. Rewrite the same tag with different NDEF content.
8. Verify the rewritten content on both mobile platforms.

The following record types have been tested:

- HTTPS URL.
- Text.
- Additional NFC Maker record types.

Scanning guidance:

- On iPhone, bring the top edge of the device close to the tag.
- On Android, bring the rear NFC antenna area close to the tag.
- The exact Android antenna position varies by model.

The Flipper Zero is a development and testing tool. End users must not be permanently required to own one in the long-term product vision.

---

### Architecture

The application begins as a modular monolith.

A single FastAPI application will contain:

- Public HTTP routes.
- Authenticated management routes.
- Server-rendered pages.
- Business logic.
- Database access.
- Static assets.

Current structure:

```text
src/nfc_hub/
├── __init__.py
├── main.py
└── core/
    ├── __init__.py
    ├── database.py
    └── settings.py
```

Database migration infrastructure:

```text
alembic.ini
alembic/
├── env.py
├── script.py.mako
└── versions/
```

Expected structure as functionality is introduced:

```text
src/nfc_hub/
├── __init__.py
├── main.py
├── api/
├── core/
├── models/
├── schemas/
├── services/
├── templates/
└── static/
```

Directories and modules must only be created when required by an implemented feature.

---

### Main Responsibilities

#### `main.py`

- Create and configure the FastAPI application.
- Load centralized application settings.
- Register routers.
- Configure templates and static files when introduced.
- Avoid containing business logic.

#### `api/`

- Define public and authenticated routes.
- Handle HTTP-specific validation and responses.
- Delegate non-trivial business logic.

#### `core/`

- Hold application configuration.
- Provide shared security or database infrastructure when required.
- Avoid becoming a miscellaneous utility directory.

#### `core/settings.py`

- Define application settings through `AppSettings`.
- Load configurable values from environment variables using the `NFC_HUB_` prefix.
- Obtain the application version from installed package metadata.
- Expose a cached settings instance through `get_settings()`.

#### `core/database.py`

- Create SQLAlchemy engines through `build_engine()`.
- Configure the application database engine.
- Expose the `SessionLocal` session factory.
- Expose the declarative `Base` for persistence models.
- Apply database-specific engine configuration when required.
- Avoid creating application tables automatically.

#### `models/`

- Define SQLAlchemy database entities.
- Express relationships and database constraints.

#### `schemas/`

- Define Pydantic request and response schemas.
- Validate external input.

#### `services/`

- Contain business rules that do not belong directly in route handlers.
- Enforce operations such as tag creation, ownership checks and destination updates.

#### `templates/`

- Contain Jinja2 HTML templates.
- Use Spanish for user-facing text.

#### `static/`

- Contain CSS, minimal JavaScript and local images.

---

### Application Configuration

Application settings are centralized in:

```text
src/nfc_hub/core/settings.py
```

The application version is obtained from the installed package metadata for `nfc-hub`. It must not be duplicated as a hardcoded value in the application code.

Example environment configuration:

```bash
export NFC_HUB_APP_NAME="NFC Hub Local"
export NFC_HUB_ENVIRONMENT="development"
export NFC_HUB_DEBUG="true"
export NFC_HUB_DATABASE_URL="sqlite:///./nfc_hub.db"
```

Settings are exposed through a cached `get_settings()` function. Tests that modify environment variables must clear the settings cache before and after execution.

Authentication secrets and deployment-specific credentials must only be introduced when required by their corresponding increments.

---

### Database Infrastructure

The database infrastructure uses SQLAlchemy 2.x.

The application exposes:

- `build_engine()` for constructing an engine from a database URL.
- `engine` as the configured application engine.
- `SessionLocal` as the application session factory.
- `Base` as the declarative base for future models.

The module-level engine and session factory must not open a connection or create the SQLite database merely by being imported.

SQLite uses thread-compatible connection configuration because FastAPI may execute request handling across different threads.

Tests must use isolated in-memory or temporary databases and must not create or modify the development database.

Database schema changes must be managed using Alembic. Application code must not use `Base.metadata.create_all()` as a substitute for migrations.

---

### Alembic

Alembic is configured at the project root:

```text
alembic.ini
alembic/
```

The effective database URL is obtained from `AppSettings`, keeping the application configuration as the single source of truth.

No migration revision exists yet because no persistence model has been implemented.

The first revision must be created alongside the first database model. Empty or speculative migrations must not be created.

Useful validation commands:

```bash
alembic check
alembic current
```

---

### Main Commands

Commands must be executed from the repository root.

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment on macOS and Linux:

```bash
source .venv/bin/activate
```

Install the project in editable mode with its development and testing dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Install only the project and its runtime dependencies in editable mode:

```bash
python3 -m pip install -e .
```

Verify the package installation:

```bash
python3 -m pip show nfc-hub
```

Run tests:

```bash
python3 -m pytest -v
```

Run the application:

```bash
uvicorn nfc_hub.main:app --reload
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Validate Alembic:

```bash
alembic check
alembic current
```

Commands must be updated if the application entry point or packaging configuration changes.

---

### Development Notes

#### General Development

- Use small, focused increments.
- Do not implement the complete MVP in one task.
- Add tests alongside behavior changes.
- Keep documentation aligned with implemented functionality.
- Avoid premature abstractions.
- Avoid creating empty architectural layers.
- Prefer explicit and readable code.

#### Data Storage

- SQLite is used for initial local development.
- PostgreSQL is planned for later deployment.
- Database schema changes must use Alembic.
- `create_all()` must not replace migrations.
- Tests must use isolated databases.
- Local database files must not be committed.

#### Frontend

- The initial frontend is server-rendered.
- The interface must be mobile-first.
- User-facing text must be written in Spanish.
- JavaScript must remain minimal.
- Authorization must always be enforced by the backend.

#### External URLs

- The initial tag destination must use HTTPS.
- URL validation rules must be defined and tested before destination editing is considered complete.
- Potentially dangerous schemes must be rejected, including:

```text
javascript:
data:
file:
```

- Handling of local network addresses and redirect safety must be reviewed during implementation.

#### Privacy

- The initial version should collect only the data required for account and tag management.
- Advanced scan tracking, fingerprinting or precise location collection is not part of the MVP.

---

### Incremental Development Plan

The project should be developed through small increments.

Suggested order:

1. Validate the generated FastAPI project and add a health endpoint. Completed.
2. Add packaging and test infrastructure. Completed.
3. Add application configuration. Completed.
4. Introduce SQLAlchemy and Alembic. Completed.
5. Create the first persistence model and migration.
6. Decide and implement authentication.
7. Create the remaining tag ownership model.
8. Generate secure public tag tokens.
9. Add authenticated tag creation.
10. Add the public tag resolution route.
11. Add destination editing.
12. Add tag activation and deactivation.
13. Add the server-rendered management interface.
14. Add final NFC writing instructions.
15. Prepare the first usable release.

The exact order of the first persistence models must be decided before implementation. The current product direction favors implementing the central `Tag` concept next so the project can begin exercising its NFC-specific workflow, while ownership and authentication remain required before management operations are exposed.

This order is a proposal, not permission to implement multiple increments at once.

Each increment must be reviewed before starting the next one.

---

### Roadmap

#### Planned

- Design and implement the first persistence model.
- Create the first Alembic migration.
- Define the public tag token format and length.
- Implement user persistence.
- Define the authentication and session strategy.
- Implement secure authentication.
- Implement logical NFC tag management.
- Generate permanent public tag URLs.
- Implement configurable HTTPS redirects.
- Implement tag activation and deactivation.
- Add a mobile-first management interface.
- Document the complete Flipper Zero writing workflow.
- Test the complete application workflow with physical NTAG215 tags.

#### In Progress

- Nothing in progress at the moment.

#### Completed

- Generate the initial project structure.
- Configure the repository with `main` and `develop`.
- Define the project scope and development rules.
- Normalize the Python package as `src/nfc_hub`.
- Create and validate the minimal FastAPI application.
- Add the `GET /health` endpoint.
- Add initial automated tests.
- Add project packaging using `pyproject.toml`.
- Configure editable installation for the `src` layout.
- Separate runtime and testing dependencies.
- Centralize pytest configuration.
- Enable package imports without configuring `PYTHONPATH`.
- Add centralized application settings using `AppSettings`.
- Add environment-variable support using the `NFC_HUB_` prefix.
- Configure the FastAPI title, version and debug mode through settings.
- Resolve the application version from installed package metadata.
- Introduce SQLAlchemy 2.x.
- Configure SQLite for local development.
- Add configurable database URL support.
- Add the application engine and session factory.
- Add the declarative base for future models.
- Configure Alembic.
- Validate Alembic using real command execution.
- Expand the automated test suite to 20 tests.
- Confirm NTAG215 hardware specifications.
- Write NDEF records using Flipper Zero and Momentum.
- Validate physical tag scanning on Android.
- Validate physical tag scanning on iPhone.
- Confirm that physical tags can be rewritten successfully.
- Validate URL, text and additional NDEF record types.

---

### Future Possibilities

The following ideas may be considered after the MVP is stable:

- Multiple destination or action types.
- QR code equivalents for NFC tags.
- Basic scan statistics.
- Privacy-conscious analytics.
- Tag ownership transfers.
- Temporary tag destinations.
- Scheduled destination changes.
- Contact card pages.
- Emergency information pages.
- Social or portfolio link pages.
- Custom public slugs.
- Custom domains.
- Native mobile NFC writing.
- Guided NFC writing workflows.
- PostgreSQL deployment.
- Docker-based deployment.
- Raspberry Pi deployment experiments.

These are possibilities, not current requirements.

---

### Known Issues

- The authentication and session strategy has not been selected yet.
- The final public token length and format have not been selected yet.
- No persistence models or database tables exist yet.
- No Alembic migration revisions exist yet.
- Direct NFC writing from the application is not supported.
- Physical tags currently require an external writing tool.
- NFC antenna position varies between mobile devices.

---

### Release Notes Context

Important context for the v0.4.0 release:

- NFC Hub now includes database infrastructure using SQLAlchemy 2.x.
- SQLite is the default database for local development.
- The database URL can be configured through `NFC_HUB_DATABASE_URL`.
- The application exposes a configurable engine and session factory.
- A declarative base is available for future persistence models.
- Alembic is configured for future database migrations.
- No models, application tables or migration revisions have been created yet.
- The complete test suite contains 20 passing tests.
- Alembic integration is validated through actual command execution.
- Tests use isolated in-memory or temporary databases.
- Importing the database module does not create `nfc_hub.db`.
- NTAG215 tags have been written and rewritten successfully.
- NDEF records have been scanned successfully using Android and iPhone.
- The first supported application behavior will be configurable HTTPS redirection.
- Security is based on authenticated ownership, not NFC UID or URL secrecy.

New implementation changes made after this release must be recorded under:

```text
### [Unreleased]
```

in `CHANGELOG.md`.

---

### Notes for Future Agents

Before making changes:

1. Read `AGENT.md`.
2. Read this file completely.
3. Inspect the current repository structure.
4. Check the current branch and Git status.
5. Verify what functionality is actually implemented.
6. Distinguish roadmap items from implemented features.
7. Propose one small, coherent increment.
8. Explain architectural or security implications.
9. Wait for approval when the requested scope is ambiguous.
10. Run and report the relevant tests after making changes.

Important restrictions:

- Do not implement the entire MVP in one task.
- Do not introduce a separate frontend.
- Do not introduce Docker before it is requested.
- Do not treat the NFC UID as proof of ownership.
- Do not make public tokens predictable.
- Do not expose internal database identifiers.
- Do not add speculative domain models.
- Do not create empty migrations.
- Do not use `create_all()` instead of Alembic migrations.
- Do not claim security guarantees without implementation and tests.
- Do not create commits, merges, tags or pushes unless explicitly requested.

The project must remain understandable, testable and defensible at every stage.