
## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

### [Unreleased]

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