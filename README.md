# interactive-video-labs-core 

<p align="center">
  <img src="https://raw.githubusercontent.com/interactive-video-labs/docs/main/logo.svg" width="200" alt="Interactive Video Labs Logo" />
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/interactive-video-labs-core" alt="PyPI Version" />
  <img src="https://img.shields.io/pypi/l/interactive-video-labs-core" alt="License" />
  <img src="https://img.shields.io/pypi/dm/interactive-video-labs-core" alt="PyPI Downloads" />
</p>

Framework-agnostic Python backend core and storage adapters for syncing interactive video state and decision ledgers.

The package is designed to complement [`@interactive-video-labs/core`](https://github.com/interactive-video-labs/interactive-video-core), the framework-agnostic TypeScript player used by interactive video applications.

---

## Features

- **Decision ledger:** Persist each user choice with session, video, node, choice, playback timestamp, and optional metadata.
- **Session resume:** Reconstruct the latest node and playback timestamp for a user session.
- **Transition validation:** Verify that a submitted choice belongs to the choices allowed for the current node.
- **Pydantic models:** Use typed, validated submission and resume response models.
- **Live session protocol:** Validate versioned WebSocket event schemas and build room snapshots and decision tallies.
- **Async SQLAlchemy storage:** Work with async database sessions and SQLAlchemy 2.x.
- **Framework agnostic:** Integrate the core with FastAPI, Django, Litestar, or another Python backend.
- **Chronological state recovery:** Rebuild state even when decision records arrive out of order.

---

## Requirements

- Python 3.10 or newer
- Pydantic 2.x
- SQLAlchemy 2.x

---

## Installation

### Poetry

```bash
poetry add interactive-video-labs-core
```

### pip

```bash
pip install interactive-video-labs-core
```

---

## Quick Start

### 1. Create the database tables

```python
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from interactive_video_backend_core.orm_models import Base


engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///./interactive_video.db"
)

async def initialize_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
```

### 2. Save a decision

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from interactive_video_backend_core.models import DecisionSubmission
from interactive_video_backend_core.storage_sqlalchemy import (
    SQLAlchemySessionRepository,
)

session_factory = async_sessionmaker(engine, class_=AsyncSession)


async def save_decision():
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
```

### 3. Restore session state

```python
async def resume_session():
    async with session_factory() as session:
        repository = SQLAlchemySessionRepository(session)
        state = await repository.get_session_state(
            user_id="user-123",
            session_id="session-456",
        )

    if state is not None:
        print(state.last_node_id)
        print(state.last_timestamp)
        print(state.decision_history)
```

The repository returns `None` when no decision exists for the supplied user and session.

---

## Decision Transition Validation

Use `DecisionLedgerEngine.validate_transition()` when a node defines the choices that may be selected:

```python
from interactive_video_backend_core.logic import DecisionLedgerEngine

DecisionLedgerEngine.validate_transition(
    current_node="question-1",
    choice_id="answer-b",
    allowed_choices=["answer-a", "answer-b"],
)
```

An invalid choice raises `ValueError`:

```text
Invalid choice 'answer-c' for node 'question-1'.
```

---

## State Reconstruction

`DecisionLedgerEngine.reconstruct_state()` returns the last node and playback timestamp according to chronological playback time:

```python
from interactive_video_backend_core.logic import DecisionLedgerEngine

node_id, timestamp = DecisionLedgerEngine.reconstruct_state(decisions)
```

If the decision list is empty, the engine returns `("start", 0.0)`.

---

## Framework-Agnostic Live Sync

The `interactive_video_backend_core.live` module defines versioned Pydantic event models and helpers for room state, playback sync, cue and node transitions, decision submissions, poll tallies, analytics updates, and presence updates. It contains no HTTP or WebSocket server dependency; mount a native endpoint in your framework and use these models and helpers inside its message handler.

All live events use protocol `version = 1`. The `LiveSessionEvent` union uses the event `type` as a Pydantic discriminator, and invalid event types or payload fields raise Pydantic validation errors.

| Event type | Purpose |
| --- | --- |
| `room:state` | Reconnect snapshot for a room |
| `playback:sync` | Shared playback position and state |
| `cue:triggered` | Cue activation |
| `node:entered` | Interactive node activation |
| `decision:submitted` | A viewer choice submission |
| `poll:tally` | Choice totals for a node |
| `analytics:updated` | Decision totals and tallies for a video |
| `presence:update` | Viewer join or leave state |

Build a reconnect snapshot from the host application's current playback state and the room's decision ledger:

```python
from datetime import datetime, timezone

from interactive_video_backend_core.live import build_room_state

snapshot = build_room_state(
    room_id="room-1",
    session_id="session-1",
    video_id="video-1",
    segment_id="segment-2",
    anchor_timestamp=42.5,
    server_timestamp=datetime.now(timezone.utc),
    playback_state="playing",
    active_cue_id="cue-3",
    participant_count=4,
    decisions=room_decisions,
)
await send_json(snapshot.model_dump(mode="json"))
```

The builder scopes decision aggregates to the requested video and reconstructs the active node from the latest decision when one is not supplied. The host remains responsible for loading playback state, participant count, and the room's decisions; the repository contract intentionally remains user/session based.

Persist an incoming decision and prepare events for the connected clients:

```python
from pydantic import TypeAdapter

from interactive_video_backend_core.live import (
    DecisionSubmittedEvent,
    LiveSessionEvent,
    handle_decision_submitted,
)

event = TypeAdapter(LiveSessionEvent).validate_json(message_json)
if isinstance(event, DecisionSubmittedEvent):
    updates = await handle_decision_submitted(
        event,
        repository,
        previous_decisions=room_decisions,
    )
    await broadcast_json(updates.poll_tally.model_dump(mode="json"))
    await broadcast_json(updates.analytics_updated.model_dump(mode="json"))
```

Load `previous_decisions` from the relevant room and exclude the incoming decision. The handler persists before returning aggregate events; repository errors propagate to the adapter. Other event models can likewise be validated and routed by the host's framework-specific WebSocket endpoint.

The module also provides `aggregate_decision_tallies()` for node-and-choice counts and `build_poll_tally()` for one node. Both helpers can be used independently of the repository:

```python
from interactive_video_backend_core.live import (
    aggregate_decision_tallies,
    build_poll_tally,
)

tallies = aggregate_decision_tallies(
    room_decisions,
    video_id="video-1",
)

poll_tally = build_poll_tally(
    room_id="room-1",
    video_id="video-1",
    node_id="question-1",
    decisions=room_decisions,
)
```

---

## Storage Interface

`AbstractSessionRepository` defines the framework-independent persistence contract:

```python
from interactive_video_backend_core.models import (
    DecisionSubmission,
    SessionResumeResponse,
)
from interactive_video_backend_core.storage import AbstractSessionRepository


class MySessionRepository(AbstractSessionRepository):
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

Implement this interface when your application needs a different database, API-backed store, or custom persistence behavior.

---

## Data Models

### `DecisionSubmission`

| Field | Type | Description |
| --- | --- | --- |
| `user_id` | `str` | Identifier of the viewer |
| `session_id` | `str` | Identifier of the viewing session |
| `video_id` | `str` | Identifier of the interactive video |
| `node_id` | `str` | Node or checkpoint reached by the viewer |
| `choice_id` | `str` | Selected branch or answer |
| `timestamp` | `float` | Playback timestamp in seconds |
| `metadata` | `dict[str, Any] \| None` | Optional application-specific metadata |

### `SessionResumeResponse`

| Field | Type | Description |
| --- | --- | --- |
| `user_id` | `str` | Identifier of the viewer |
| `session_id` | `str` | Identifier of the viewing session |
| `video_id` | `str` | Identifier of the most recently recorded video |
| `last_node_id` | `str` | Latest reconstructed node |
| `last_timestamp` | `float` | Latest reconstructed playback timestamp |
| `decision_history` | `list[DecisionSubmission]` | Decisions ordered by playback timestamp |
| `updated_at` | `datetime` | Timestamp of the latest database record |

---

## SQLAlchemy Schema

The included ORM model stores decisions in the `ivl_decision_ledger` table:

- `id`
- `user_id`
- `session_id`
- `video_id`
- `node_id`
- `choice_id`
- `timestamp`
- `metadata_json`
- `created_at`

Indexes are created for `user_id` and `session_id` to support session state lookup.

---

## Development

Clone the repository and install the development dependencies:

```bash
git clone https://github.com/interactive-video-labs/interactive-video-backend-core.git
cd interactive-video-backend-core
poetry install
```

Run the test suite:

```bash
poetry run pytest
```

For linting and project conventions, see [DEVELOPER.md](DEVELOPER.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

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
└── README.md
```

---

## Contributing

Contributions are welcome. Please review [CONTRIBUTING.md](CONTRIBUTING.md) before submitting an issue or pull request.

---

## License

This project is licensed under the [MIT License](LICENSE).
