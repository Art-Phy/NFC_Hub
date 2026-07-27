
## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).


### [Unreleased] - 2026-07-27

#### Added

- Minimal FastAPI application in the `src/nfc_hub` package.
- `GET /health` endpoint returning `{"status": "ok"}`.
- Automated tests for the health endpoint status code and JSON response.
- pytest and HTTPX as testing dependencies.
- Initial project scope and development guidelines.
