
## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

### [Unreleased]

---

### [0.6.0] - 2026-09-19

#### Added

- Persistent `Session` model for anonymous and authenticated sessions, with token hashes, CSRF tokens, user associations and expiration times.
- Alembic migration for the sessions table.
- Configurable session cookie name, cookie security, session lifetimes and allowed authentication origins.
- Argon2id password hashing, verification and automatic rehashing of outdated hashes during login.
- Secure random session and CSRF token generation.
- SHA-256 hashing of session tokens before database storage.
- Timing-safe CSRF token comparison.
- Services for creating, validating, revoking and cleaning up expired sessions.
- User registration service with email normalization, duplicate detection and password hashing.
- User authentication service with a shared error for unknown emails, incorrect passwords and inactive accounts.
- FastAPI dependencies for database sessions, current sessions, authenticated users and CSRF validation.
- Request and response schemas for registration, login and public user data.
- `POST /auth/register` to create a user and authenticated session in one transaction.
- `POST /auth/login` to authenticate a user and create a new session.
- `POST /auth/logout` to revoke the current session and clear its cookie.
- `GET /auth/me` to retrieve the authenticated user and current CSRF token.
- HTTP-only session cookies with `SameSite=lax`, configurable `Secure` and expiration aligned with the authenticated session lifetime.
- Authentication request checks requiring JSON and validating supplied `Origin` headers against configured origins.
- Automated unit, API and database-backed integration tests for complete authentication flows.

#### Changed

- Expanded the automated suite from 40 to 199 tests.
- Restricted session lifetime settings to positive values.
- Required secure session cookies when the environment is set to production.
- Added `Cache-Control: no-store` to authentication responses containing session data.
- Distinguished duplicate email conflicts from unrelated database integrity failures.
- Updated project dependencies with `argon2-cffi` and `email-validator`.
- Updated project documentation with authentication setup, API usage and current security scope.
- Updated the project version to `0.6.0`.

---

### [0.5.0] - 2026-08-07

#### Added

- First persistent application model: `User`.
- Modern SQLAlchemy 2.x model using `Mapped` and `mapped_column`.
- Required email field with a unique database index.
- ORM email normalization through whitespace trimming and lowercase conversion.
- Required storage field for password hashes.
- Active-user status with Python-side and database-side defaults.
- Timezone-aware UTC timestamps for user creation and updates.
- Automatic `updated_at` changes on normal ORM updates.
- First real Alembic revision for creating the `users` table and its unique email index.
- Reversible migration operations through `upgrade()` and `downgrade()`.
- Model registration in Alembic metadata for migration autogeneration.
- Isolated automated tests for the `User` model and database constraints.
- Migration tests covering upgrades, downgrades and complete migration round trips.
- Alembic consistency checks for detecting pending schema changes.
- Protection against creating or modifying the development database during tests.

#### Changed

- Expanded the automated test suite from 20 to 40 tests.
- Updated project documentation with the first persistence model and migration workflow.
- Updated the project version to `0.5.0`.

---

### [0.4.0] - 2026-07-31

#### Added

- Database infrastructure using SQLAlchemy 2.x.
- Configurable database URL through `AppSettings`.
- Environment-variable support for `NFC_HUB_DATABASE_URL`.
- SQLite as the default database for local development.
- `build_engine()` factory for creating SQLAlchemy engines.
- Application-level SQLAlchemy engine and `SessionLocal` session factory.
- Declarative base prepared for future persistence models.
- Initial Alembic configuration for database migrations.
- Runtime dependencies on SQLAlchemy and Alembic.
- Automated tests for database settings, engine creation and connectivity.
- Automated validation of the application session binding.
- SQLite cross-thread connection test using an isolated temporary database.
- End-to-end Alembic configuration tests.
- Database file exclusions in `.gitignore`.
- Physical NFC validation using rewritable NTAG215 tags.
- Successful NDEF record writing and rewriting using NFC Maker.
- Successful NFC tag scanning using Android and iPhone devices.

#### Changed

- Expanded the automated test suite from 9 to 20 tests.
- Updated project documentation with database infrastructure and NFC hardware validation.
- Updated the project version to `0.4.0`.

---

### [0.3.0] - 2026-07-29

#### Added

- Centralized application configuration through `AppSettings`.
- Environment-variable support using the `NFC_HUB_` prefix.
- Configurable application name, environment and debug mode.
- Automatic application version resolution from installed package metadata.
- Runtime dependency on `pydantic-settings`.
- Automated tests for default settings and environment-variable overrides.
- New `core` package for application-wide configuration.

#### Changed

- Configured the FastAPI application title, version and debug mode through centralized settings.
- Expanded the automated test suite from 2 to 9 tests.
- Updated project documentation with the application configuration workflow.

---

### [0.2.0] - 2026-07-28

#### Added

- Initial project packaging configuration using `pyproject.toml`.
- Editable installation support for the existing `src` layout.
- Centralized pytest configuration in `pyproject.toml`.
- Separate runtime and testing dependency groups.
- Project metadata including author and repository URLs.

#### Changed

- Simplified `requirements.txt` to install the project in editable mode with its testing dependencies.
- Removed the need to configure `PYTHONPATH` when running the application or test suite.
- Updated project documentation with the new installation and execution workflow.

---

### [0.1.0] - 2026-07-27

#### Added

- Initial project structure.
- Minimal FastAPI application in the `src/nfc_hub` package.
- `GET /health` endpoint returning `{"status": "ok"}`.
- Automated tests for the health endpoint status code and JSON response.
- pytest and HTTPX as testing dependencies.
- Initial project scope and development guidelines.