<p align="center">
  <img src="https://raw.githubusercontent.com/interactive-video-labs/docs/main/logo.svg" width="200" alt="Interactive Video Labs Logo" />
</p>

# Contributing

Thank you for your interest in contributing to `interactive-video-backend-core`.

We welcome improvements to the models, decision logic, SQLAlchemy storage, tests, documentation, and developer tooling. Contributions should be focused, well tested, and compatible with Python 3.10 and newer.

---

## Ways to Contribute

You can contribute in many ways:

- Report bugs or unexpected behavior.
- Add or improve Pydantic models.
- Improve transition validation or session state reconstruction.
- Add repository implementations for other storage backends.
- Improve the SQLAlchemy implementation.
- Add unit or integration tests.
- Improve documentation and examples.
- Fix formatting, typing, or dependency issues.

Please open an issue before starting a large feature or API change.

---

## Development Setup

### Prerequisites

- Python 3.10 or newer
- Poetry
- Git

### Clone the Repository

```bash
git clone https://github.com/interactive-video-labs/interactive-video-backend-core.git
cd interactive-video-backend-core
```

### Install Dependencies

```bash
poetry install
```

### Enter the Virtual Environment

```bash
poetry shell
```

Alternatively, prefix project commands with `poetry run`.

---

## Project Structure

```text
interactive-video-backend-core/
├── interactive_video_backend_core/
│   ├── __init__.py
│   ├── logic.py
│   ├── models.py
│   ├── orm_models.py
│   ├── storage.py
│   └── storage_sqlalchemy.py
├── tests/
│   ├── conftest.py
│   ├── test_logic.py
│   └── test_storage.py
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

### Core Modules

- `models.py` contains Pydantic submission and response models.
- `logic.py` contains framework-independent decision logic.
- `orm_models.py` contains SQLAlchemy ORM models.
- `storage.py` contains the abstract repository interface.
- `storage_sqlalchemy.py` contains the SQLAlchemy repository implementation.

Keep framework-independent logic separate from database-specific code.

---

## Making Changes

1. Create a focused branch from the latest default branch.
2. Make the smallest complete change that solves the problem.
3. Follow existing naming and code organization conventions.
4. Add or update tests for behavior changes.
5. Run the relevant test suite and lint checks.
6. Update documentation and type hints when public behavior changes.

### Branch Names

Use descriptive branch names, such as:

```text
fix/session-resume-order
feature/postgres-repository
docs/improve-installation-guide
test/storage-edge-cases
```

---

## Running Tests

Run the complete test suite:

```bash
poetry run pytest
```

Run a specific test file:

```bash
poetry run pytest tests/test_logic.py
poetry run pytest tests/test_storage.py
```

Run a specific test:

```bash
poetry run pytest tests/test_logic.py::test_reconstruct_state_orders_chronologically
```

Tests use an in-memory asynchronous SQLite database, so SQLAlchemy changes should work through the existing async session fixture where possible.

---

## Code Style

This project uses Ruff configuration from `pyproject.toml`.

Run the configured linter:

```bash
poetry run ruff check .
```

Apply supported automatic fixes:

```bash
poetry run ruff check . --fix
```

When writing Python code:

- Follow PEP 8 conventions.
- Use clear, descriptive names.
- Add type hints to public methods and interfaces.
- Prefer small, testable functions.
- Avoid unrelated formatting or refactoring.
- Do not add framework-specific behavior to framework-independent modules.
- Use Pydantic models for public submission and response data.
- Use async repository methods consistently.

---

## Testing Guidelines

Add tests for:

- New public behavior.
- Validation and error paths.
- Chronological ordering.
- Empty or missing session states.
- SQLAlchemy save and retrieve operations.
- Regression scenarios reported in issues.

Keep tests isolated and avoid sharing mutable state between test cases. The async database fixture creates a fresh in-memory database for each test.

A useful test structure is:

```python
@pytest.mark.asyncio
async def test_save_and_retrieve_session_state(async_db_session):
    # Arrange
    repository = SQLAlchemySessionRepository(async_db_session)

    # Act
    await repository.save_decision(decision)
    state = await repository.get_session_state(
        "user-123",
        "session-456",
    )

    # Assert
    assert state is not None
```

---

## Adding a Storage Implementation

Storage implementations should inherit from `AbstractSessionRepository` and implement:

```python
async def save_decision(
    self,
    decision: DecisionSubmission,
) -> None:
    ...

async def get_session_state(
    self,
    user_id: str,
    session_id: str,
) -> SessionResumeResponse | None:
    ...
```

Your implementation should:

- Persist decisions without losing submitted fields.
- Preserve optional decision metadata.
- Retrieve data only for the specified user and session.
- Return `None` when no session data exists.
- Reconstruct the latest state consistently.
- Document any database migrations or schema requirements.

Do not expose framework-specific database sessions through the public storage interface unless it is explicitly defined for that implementation.

---

## Updating the Data Models

Public Pydantic or ORM model changes may affect both storage and downstream applications.

Before changing a field:

- Confirm whether it is backward-compatible.
- Update `DecisionSubmission` and `SessionResumeResponse` together if required.
- Update `DecisionModel` and repository conversion code for ORM changes.
- Add migration guidance for persisted data.
- Update tests and README examples.

Fields should have clear names and types, and optional fields should use `Optional[...]` or `T | None` consistently.

---

## Documentation

Update documentation when you:

- Add or rename public APIs.
- Change storage behavior.
- Change configuration or dependencies.
- Add setup requirements.
- Add a new integration or repository implementation.

Keep code examples runnable and synchronized with the current implementation.

---

## Pull Requests

Pull requests should include:

- A clear summary of the change.
- A description of why the change is needed.
- Links to related issues.
- Tests for new or modified behavior.
- Documentation updates for public API changes.
- Any migration or compatibility notes.

Before submitting:

```bash
poetry run pytest
poetry run ruff check .
git diff --check
```

Keep pull requests focused. Separate unrelated fixes and formatting changes whenever possible.

---

## Bug Reports

Please include:

- A clear description of the issue.
- Steps to reproduce it.
- Expected behavior.
- Actual behavior.
- Python and dependency versions.
- Relevant logs or stack traces.
- A minimal code example when possible.

Do not include credentials, private keys, personal data, or production database contents in bug reports or test data.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).