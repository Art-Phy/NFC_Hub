
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
v0.5.0
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
- Declarative base for persistence models.
- Persistent `User` model.
- ORM email normalization.
- Python-side and database-side defaults.
- Timezone-aware user timestamps.
- Alembic configuration for database migrations.
- First real Alembic revision for the `users` table.
- Reversible migration operations.
- Alembic model registration and autogeneration consistency.
- Isolated model and migration tests.
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

The first persistent application model is defined in:

```text
src/nfc_hub/models/user.py
```

The first Alembic revision creates the `users` table and its unique email index.

The application, editable installation, package import, health endpoint, database infrastructure, `User` model and Alembic migration have been validated successfully.

The current test suite contains 40 passing tests.

User persistence is implemented, but it is not exposed through the API. Registration, password hashing, authentication, tag persistence, tag management and public tag resolution remain planned.

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

The initial domain includes or is expected to include the following concepts.

#### User

Represents an account that will authenticate and own NFC tags.

Currently implemented fields:

- Internal integer identifier.
- Required email address.
- Unique email index.
- ORM email normalization using whitespace trimming and lowercase conversion.
- Required password hash storage field.
- Active status.
- Creation timestamp.
- Update timestamp.

Current implementation notes:

- `User` is implemented only as a persistence model.
- Password hashing logic is not implemented.
- Registration and authentication are not implemented.
- No user routes, schemas or services exist yet.
- The model does not currently own any tags because tag persistence has not been introduced.

Future responsibilities:

- Authenticate before accessing management operations.
- Own zero or more tags.
- Participate in ownership and authorization checks.

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

The `User` model stores only the future password hash. Plaintext passwords must never be persisted.

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
├── core/
│   ├── __init__.py
│   ├── database.py
│   └── settings.py
└── models/
    ├── __init__.py
    └── user.py
```

Database migration infrastructure:

```text
alembic.ini
alembic/
├── env.py
├── script.py.mako
└── versions/
    └── 2c5ceb75c9fa_create_users_table.py
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
- Keep persistence concerns separate from HTTP and authentication behavior.

#### `models/user.py`

- Define the persistent `User` entity.
- Store normalized account email addresses.
- Store password hashes without implementing hashing logic.
- Provide active status and timestamps.
- Avoid containing registration or authentication workflows.

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
- `Base` as the declarative base for persistence models.

The module-level engine and session factory must not open a connection or create the SQLite database merely by being imported.

SQLite uses thread-compatible connection configuration because FastAPI may execute request handling across different threads.

Tests must use isolated in-memory or temporary databases and must not create or modify the development database.

Database schema changes must be managed using Alembic. Application code must not use `Base.metadata.create_all()` as a substitute for migrations.

The current database schema contains the `users` table.

The `User` model uses:

- Modern SQLAlchemy 2.x typed mappings.
- A required and uniquely indexed email address.
- ORM email normalization.
- Required password hash storage.
- Python-side and database-side defaults.
- Timezone-aware creation and update timestamps.
- Automatic ORM updates for `updated_at`.

Database-side defaults use portable SQLAlchemy expressions to preserve compatibility with the planned PostgreSQL migration.

---

### Alembic

Alembic is configured at the project root:

```text
alembic.ini
alembic/
```

The effective database URL is obtained from `AppSettings`, keeping the application configuration as the single source of truth.

The first migration revision is:

```text
2c5ceb75c9fa_create_users_table.py
```

The revision creates:

- The `users` table.
- The unique `ix_users_email` index.

Its `upgrade()` and `downgrade()` operations are complete and symmetrical.

The `User` model is registered in Alembic metadata so autogeneration can compare the declared model with the migrated schema.

Apply all pending migrations:

```bash
alembic upgrade head
```

Revert all migrations:

```bash
alembic downgrade base
```

Useful validation commands after upgrading the database to `head`:

```bash
alembic check
alembic current
```

`alembic check` must report no pending schema operations when the database is at the current head revision.

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

Apply database migrations:

```bash
alembic upgrade head
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

Validate Alembic after upgrading the database to `head`:

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
- `create_all()` must not replace migrations in application code.
- Tests may use `Base.metadata.create_all()` only for isolated model-level databases when migration behavior is not under test.
- Tests must use isolated databases.
- Local database files must not be committed.
- Tests must not create or modify `nfc_hub.db`.

#### User Persistence

- Email normalization currently occurs during normal ORM assignment.
- Database-level inserts do not perform ORM normalization.
- Email uniqueness is enforced by a single unique database index.
- `password_hash` stores only an already generated hash.
- Password hashing and verification must be implemented outside the model.
- User persistence must not be described as registration or authentication.
- Authentication behavior must not be added to the model.

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
5. Create the first persistence model and migration. Completed.
6. Define the authentication, session, password hashing and CSRF strategy.
7. Implement user registration and authentication.
8. Create the tag persistence and ownership model.
9. Define and generate secure public tag tokens.
10. Add authenticated tag creation.
11. Add the public tag resolution route.
12. Add destination editing.
13. Add tag activation and deactivation.
14. Add the server-rendered management interface.
15. Add final NFC writing instructions.
16. Prepare the first usable release.

The next increment must define the authentication architecture before authentication code is implemented.

That review must cover at least:

- Server-side session strategy.
- Session storage and cookie behavior.
- Password hashing library and parameters.
- Login and logout lifecycle.
- CSRF protection requirements.
- Authentication dependencies.
- Secret configuration.
- Testing strategy.

This order is a proposal, not permission to implement multiple increments at once.

Each increment must be reviewed before starting the next one.

---

### Roadmap

#### Planned

- Define the authentication and session strategy.
- Select and configure secure password hashing.
- Implement user registration.
- Implement user authentication and logout.
- Create the tag persistence and ownership model.
- Define the public tag token format and length.
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
- Add the declarative base for persistence models.
- Configure Alembic.
- Validate Alembic using real command execution.
- Create the persistent `User` model.
- Add required and uniquely indexed user emails.
- Add ORM email normalization.
- Add password hash storage.
- Add active-user and timestamp defaults.
- Create the first real Alembic migration.
- Register persistence models in Alembic metadata.
- Verify Alembic autogeneration consistency.
- Verify migration upgrade, downgrade and re-upgrade behavior.
- Protect the development database during automated tests.
- Expand the automated test suite to 40 tests.
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
- The password hashing library and parameters have not been selected yet.
- CSRF protection requirements have not been finalized.
- User persistence is not exposed through registration or authentication workflows.
- The final public token length and format have not been selected yet.
- No tag persistence model exists yet.
- Direct NFC writing from the application is not supported.
- Physical tags currently require an external writing tool.
- NFC antenna position varies between mobile devices.

---

### Release Notes Context

Important context for the v0.5.0 release:

- NFC Hub now includes its first persistent application model: `User`.
- The model uses modern SQLAlchemy 2.x typed mappings.
- User emails are required, normalized by the ORM and protected by a unique database index.
- The model stores a required password hash without implementing password hashing or authentication logic.
- Active status and timestamps have Python-side and database-side defaults.
- `updated_at` changes automatically during normal ORM updates.
- The first real Alembic revision creates the `users` table and its unique email index.
- Migration `upgrade()` and `downgrade()` operations are implemented and verified.
- Alembic metadata registration supports schema autogeneration checks.
- Migration defaults use portable SQLAlchemy expressions compatible with SQLite and planned PostgreSQL usage.
- The complete test suite contains 40 passing tests.
- Model and migration tests use isolated in-memory or temporary databases.
- Tests do not create or modify `nfc_hub.db`.
- Registration, password hashing, authentication, tag persistence and public tag resolution remain unimplemented.
- The next increment must define the authentication, session, password hashing and CSRF strategy before authentication code is added.
- Security remains based on authenticated ownership, not NFC UID or URL secrecy.

New implementation changes made after this release must be recorded under:

```text
### [Unreleased]
```