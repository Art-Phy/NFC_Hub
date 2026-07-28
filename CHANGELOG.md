
## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).


### [Unreleased]

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
- pytest and HTTPX2 as testing dependencies.
- Initial project scope and development guidelines.