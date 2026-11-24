<p align="center">
  <img src="https://raw.githubusercontent.com/interactive-video-labs/docs/main/logo.svg" width="200" alt="Interactive Video Labs Logo" />
</p>

# interactive-video-labs-core 0.3.0 Developer Guide

This guide explains how to set up, develop, test, and publish `interactive-video-labs-core`.

Framework-agnostic Python backend core and storage adapters for syncing interactive video state and decision ledgers. The package uses Pydantic 2, SQLAlchemy 2 async APIs, and Poetry for dependency management.

---

## Prerequisites

- Python 3.10 or newer
- Poetry
- Git
- An async database driver for integration use

The test suite uses SQLite with `aiosqlite`; `aiosqlite` is included in the development dependencies.

---

## Initial Setup

Clone and enter the repository:

```bash
git clone https://github.com/interactive-video-labs/interactive-video-backend-core.git
cd interactive-video-backend-core
```

Install the package and development dependencies:

```bash
poetry install
```

Poetry creates or uses the project virtual environment automatically.

---

## Project Structure

```text
interactive-video-backend-core/
├── interactive_video_backend_core/
│   ├── __init__.py
│   ├── logic.py
│   ├── live.py
│   ├── models.py
│   ├── orm_models.py
│   ├── storage.py
│   └── storage_sqlalchemy.py
├── tests/
│   ├── conftest.py
│   ├── test_logic.py
│   ├── test_live.py
│   └── test_storage.py
├── pyproject.toml
├── README.md
├── DEVELOPER.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## Module Responsibilities

### `models.py`

Defines the public Pydantic data models:

- `DecisionSubmission`
- `SessionResumeResponse`

Use these types at repository boundaries so framework code exchanges validated, serializable data with the core package.

### `logic.py`

Contains `DecisionLedgerEngine`, a framework-independent business logic class:

- `validate_transition()` validates a choice against a node's allowed choices.
- `reconstruct_state()` returns the latest node and playback timestamp from decision submissions.

The logic module does not perform database operations.

### `live.py`

Defines versioned, framework-independent Pydantic WebSocket events and pure room snapshot/tally builders. `handle_decision_submitted()` persists through `AbstractSessionRepository`, then returns poll and analytics events using the prior room decisions supplied by the host. It does not own connection lifecycle, room membership, or room-wide ledger queries.

The public live API includes:

- `LiveSessionEvent`, a discriminated Pydantic union for protocol version 1 events.
- `RoomStateEvent` and `build_room_state()` for reconnect snapshots.
- `aggregate_decision_tallies()` for node-and-choice counts.
- `build_poll_tally()` for one node or poll.
- `handle_decision_submitted()` for persistence and broadcast updates.

The live module is intentionally framework agnostic. HTTP routing, WebSocket connection management, authentication, room membership, and room ledger loading belong in the host application.

### `orm_models.py`

Defines SQLAlchemy declarations:

- `Base`
- `DecisionModel`

The ORM stores records in the `ivl_decision_ledger` table.

### `storage.py`

Defines `AbstractSessionRepository`, the async storage contract for session repositories.

Implementations must support:

- Saving a `DecisionSubmission`
- Retrieving a `SessionResumeResponse`

### `storage_sqlalchemy.py`

Provides `SQLAlchemySessionRepository`, the async SQLAlchemy implementation:

- Generates a UUID for each persisted decision.
- Commits each submission.
- Orders stored decisions by playback timestamp.
- Reconstructs resume state through `DecisionLedgerEngine`.

---

## Running the Package

Use Poetry to execute Python or project tools:

```bash
poetry run python
poetry run python -m pytest
```

To start the package virtual environment shell:

```bash
poetry shell
```

---

## Testing

### Run the Test Suite

```bash
poetry run pytest
```

The test configuration in `pyproject.toml` uses:

- `asyncio_mode = "auto"`
- `testpaths = ["tests"]`

### Run a Specific File

```bash
poetry run pytest tests/test_logic.py
poetry run pytest tests/test_live.py
poetry run pytest tests/test_storage.py
```

### Run a Specific Test

```bash
poetry run pytest tests/test_logic.py::test_validate_transition_success
```

### Async Database Fixture

Tests create a fresh in-memory database through `tests/conftest.py`:

```python
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
)
```

The fixture:

1. Creates all SQLAlchemy tables.
2. Opens an async SQLAlchemy session.
3. Yields the session to the test.
4. Disposes the engine after the test.

Use `async_db_session` to test repository behavior:

```python
@pytest.mark.asyncio
async def test_repository(async_db_session):
    repository = SQLAlchemySessionRepository(async_db_session)
```

---

## Database Setup

Create tables before using `SQLAlchemySessionRepository`:

```python
from sqlalchemy.ext.asyncio import AsyncEngine
from interactive_video_backend_core.orm_models import Base


async def create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
```

For production databases, manage schema changes through your application's migration system. The package currently does not include an Alembic migration configuration.

---

## SQLAlchemy Example

```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from interactive_video_backend_core.models import DecisionSubmission
from interactive_video_backend_core.storage_sqlalchemy import (
    SQLAlchemySessionRepository,
)

engine = create_async_engine(
    "sqlite+aiosqlite:///./interactive_video.db"
)
session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
)


async def save_decision() -> None:
    decision = DecisionSubmission(
        user_id="user-123",
        session_id="session-456",
        video_id="video-789",
        node_id="question-1",
        choice_id="answer-b",
        timestamp=12.5,
        metadata={"source": "web"},
    )

    async with session_factory() as session:
        repository = SQLAlchemySessionRepository(session)
        await repository.save_decision(decision)


async def resume_session():
    async with session_factory() as session:
        repository = SQLAlchemySessionRepository(session)
        return await repository.get_session_state(
            "user-123",
            "session-456",
        )
```

Create tables before calling `save_decision()`.

---

## Adding a Storage Backend

Create a class that implements `AbstractSessionRepository`:

```python
from interactive_video_backend_core.models import (
    DecisionSubmission,
    SessionResumeResponse,
)
from interactive_video_backend_core.storage import AbstractSessionRepository


class ExampleRepository(AbstractSessionRepository):
    async def save_decision(
        self,
        decision: DecisionSubmission,
    ) -> None:
        raise NotImplementedError

    async def get_session_state(
        self,
        user_id: str,
        session_id: str,
    ) -> SessionResumeResponse | None:
        raise NotImplementedError
```

A custom repository should:

- Preserve all `DecisionSubmission` fields.
- Filter records by `user_id` and `session_id`.
- Use `SessionResumeResponse` for resume data.
- Return `None` when no record is found.
- Add tests for save and resume behavior.
- Document schema or external service requirements.

---

## Adding or Updating Models

Public model changes require coordinated updates:

1. Update Pydantic models in `models.py`.
2. Update ORM fields in `orm_models.py`, if persisted.
3. Update SQLAlchemy conversion code in `storage_sqlalchemy.py`.
4. Update logic code if the field affects state reconstruction.
5. Update tests and README examples.
6. Document migration or compatibility requirements.

Be aware that changing a persisted field may require a database migration in applications using the package.

---

## Code Quality

The Ruff configuration in `pyproject.toml` enables the following rule groups:

- `E` and `W`: style and formatting
- `F`: correctness and undefined names
- `I`: import sorting
- `B`: bugbear checks
- `C4`: comprehensions
- `ARG`: unused arguments
- `SIM`: simplification

Run Ruff:

```bash
poetry run ruff check .
```

Apply automatic fixes where supported:

```bash
poetry run ruff check . --fix
```

Ruff is configured as a development tool but is not listed under `[tool.poetry.group.dev.dependencies]`. Install it separately in the development environment if the command is unavailable:

```bash
poetry add --group dev ruff
```

---

## Type Checking

Pyright configuration is declared in `pyproject.toml`:

```toml
[tool.pyright]
useLibraryCodeForTypes = true
exclude = [".cache", "dist", ".venv"]
```

Run Pyright if it is available in your environment:

```bash
pyright
```

Public functions should include type hints, especially repository methods and Pydantic model fields.

---

## Build the Package

Poetry uses `poetry-core` for package builds:

```bash
poetry build
```

This generates the source distribution and wheel in `dist/`.

Create or update the package metadata only in `pyproject.toml`.

---

## Publishing

Publishing is intended to use the Poetry package workflow and requires appropriate PyPI credentials.

Before publishing:

1. Update `version` in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Run the complete test suite.
4. Run the linter.
5. Build the package.
6. Verify the generated files in `dist/`.
7. Publish after the repository's release review process.

```bash
poetry run pytest
poetry run ruff check .
poetry build
poetry publish
```

Use a version unique to the release and update the changelog before generating a release.

---

## Pre-Submission Checklist

Before opening a pull request:

```bash
poetry run pytest
poetry run ruff check .
git diff --check
```

Confirm that:

- Tests cover changed behavior.
- Public models and documentation remain consistent.
- Database changes include migration guidance.
- Framework-specific code remains outside the core logic module.
- No credentials or private database contents appear in tests or examples.
- The README and developer documentation reflect the current implementation.

---

## Further Reading

- [README.md](README.md) for package usage.
- [CONTRIBUTING.md](CONTRIBUTING.md) for contribution expectations.
- [CHANGELOG.md](CHANGELOG.md) for release history.