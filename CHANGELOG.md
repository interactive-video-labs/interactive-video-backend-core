<p align="center">
  <img src="https://raw.githubusercontent.com/interactive-video-labs/docs/main/logo.svg" width="200" alt="Interactive Video Labs Logo" />
</p>

# Changelog

All notable changes to `interactive-video-backend-core` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Improved project documentation for installation, usage, development, and contribution workflows.

### Changed

- No unreleased changes.

### Deprecated

- No deprecated features.

### Removed

- No removed features.

### Fixed

- No fixed issues.

### Security

- No security updates.

---

## [0.1.0] - 2026-11-18

### Added

- Initial `interactive-video-backend-core` Python package.
- Pydantic `DecisionSubmission` model for interactive video decisions.
- Pydantic `SessionResumeResponse` model for resumed session state.
- `DecisionLedgerEngine` for choice transition validation.
- Chronological session-state reconstruction from decision submissions.
- `AbstractSessionRepository` async storage interface.
- `SQLAlchemySessionRepository` async SQLAlchemy implementation.
- SQLAlchemy `DecisionModel` for the `ivl_decision_ledger` table.
- UUID-based decision identifiers.
- Optional JSON decision metadata support.
- Async SQLite test database fixture.
- Unit tests for transition validation and state reconstruction.
- Unit tests for SQLAlchemy save and session-state retrieval.
- Package configuration with Python 3.10 support.
- Pydantic 2 and SQLAlchemy 2 dependency support.
- Poetry build configuration.
- MIT license.
- README, developer, and contribution documentation.

### Changed

- No prior versions.

### Fixed

- No prior releases.

---

## Release Links

- [Unreleased](https://github.com/interactive-video-labs/interactive-video-backend-core/compare/v0.1.0...HEAD)
- [0.1.0](https://github.com/interactive-video-labs/interactive-video-backend-core/releases/tag/v0.1.0)