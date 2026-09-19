
# NFC Hub — Project Context

NFC Hub is a FastAPI application for managing reusable NFC tags. Each physical tag will contain a permanent public URL. Its owner will be able to change the URL's destination in the application without rewriting the tag.

This file records product scope and domain decisions. See `README.md` for installation and API usage, `CHANGELOG.md` for release history, and `AGENT.md` for development conventions.

## Current status

Version **v0.6.0** establishes the account and authentication foundation. The automated suite contains **199 tests**.

Implemented:

- FastAPI application with `GET /health` and interactive API documentation.
- Centralized settings through `AppSettings` and `NFC_HUB_` environment variables.
- SQLAlchemy models for users and sessions, with Alembic migrations.
- Registration, login, logout and current-user endpoints under `/auth`.
- Argon2id password hashing and automatic rehashing of outdated hashes at login.
- Server-side sessions with random tokens; only token hashes are stored in the database.
- Expiring sessions, `HttpOnly` cookies, CSRF validation and authentication origin checks.
- Unit, API, migration and database-backed authentication integration tests.
- Physical NTAG215 writing, rewriting and scanning validated with Android and iPhone.

Not yet implemented: tag records, ownership management, public tag URLs, destination redirects or a management interface. Authentication has not yet been prepared for public deployment with HTTPS and attempt limiting.

## Product goal

A user should be able to:

1. Create an account and sign in.
2. Register a logical NFC tag.
3. Assign it an external HTTPS destination.
4. Write its permanent public URL to a physical tag.
5. Change the destination without rewriting the physical tag.
6. Activate or deactivate the tag.
7. Manage only tags they own.

The first supported public behavior will be a redirect to one external HTTPS URL per tag.

## Domain rules

The following are separate concepts:

- **Physical tag:** the NFC object containing an NDEF URL record.
- **Public URL:** a stable link such as `https://example.com/t/{public_token}`.
- **Owner:** the authenticated user permitted to manage the logical tag.
- **Destination:** the current external HTTPS URL resolved by the backend.

Public tag tokens must be random, URL-safe, non-sequential, difficult to guess and unique in the database. They must not reveal internal IDs. Their final format and length will be chosen when tag creation is implemented.

The public URL and NFC UID are not secrets or proof of ownership. A visitor may scan or copy a tag URL, but this must never grant access to management operations. Every protected tag operation must check ownership on the server.

Changing a destination must preserve the public URL already written to the physical tag. An inactive or unknown tag must produce a clear public response without exposing internal data.

For the initial version, one destination can be stored directly with each tag. A separate destination or action model is unnecessary until multiple behaviors are required.

## MVP scope

The first usable tag-management version should include:

- Authenticated tag creation and management.
- An owner relationship and authorization checks.
- Secure generation and persistence of permanent public tokens.
- Validation of external HTTPS destinations.
- Public resolution and redirect for active tags.
- Tag activation and deactivation.
- A simple, mobile-friendly management interface.
- Tests for ownership, invalid input, inactive tags and public resolution.
- Instructions for writing a generated URL to a physical NTAG215 tag.

The interface is planned; its exact implementation should be chosen when that increment begins. NFC Hub does not need to write tags directly from the browser for the MVP.

## Outside the MVP

Do not add these without a separate decision: native mobile apps, direct browser NFC writing, social login, email verification, password recovery, ownership transfer, team accounts, subscriptions, advanced analytics, geolocation tracking, webhooks, custom domains, multiple actions per tag, Redis, microservices or custom cryptography.

PostgreSQL and Docker may be considered for a later deployment phase. SQLite remains the local development database.

## Hardware validation

Initial hardware: **NTAG215**, NFC Forum Type 2, with 504 bytes of usable memory. NDEF records have been written and rewritten using a Flipper Zero with Momentum firmware and NFC Maker. Scanning has been validated on Android and iPhone.

The normal NFC Hub workflow will write only the permanent public URL to the tag. The Flipper Zero is a development tool; owning one should not become a requirement for every future user.

## Architecture and next increments

NFC Hub remains a modular FastAPI application:

- `main.py` creates the application and registers routers.
- `api/` handles HTTP requests and responses.
- `schemas/` validates external input and output.
- `models/` defines SQLAlchemy entities.
- `core/` contains shared configuration, database and authentication infrastructure.
- Alembic owns database schema changes.

Next increments, one at a time:

1. Define the tag model, ownership relationship and migration.
2. Choose the public token format and implement tag creation.
3. Add the public resolution route and HTTPS destination validation.
4. Add destination editing and tag activation controls.
5. Build the management interface and test the complete physical workflow.

Keep this plan current as decisions are made. Planned functionality should never be described as already implemented.