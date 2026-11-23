from datetime import datetime, timezone

import pytest
from pydantic import TypeAdapter

from interactive_video_backend_core.live import (
    DecisionSubmittedEvent,
    DecisionSubmittedPayload,
    LiveSessionEvent,
    aggregate_decision_tallies,
    build_room_state,
    handle_decision_submitted,
)
from interactive_video_backend_core.models import DecisionSubmission
from interactive_video_backend_core.storage_sqlalchemy import SQLAlchemySessionRepository


def _decision(
    *,
    user_id: str,
    video_id: str = "video-1",
    node_id: str = "poll-1",
    choice_id: str = "choice-a",
    timestamp: float = 1.0,
) -> DecisionSubmission:
    return DecisionSubmission(
        user_id=user_id,
        session_id=f"session-{user_id}",
        video_id=video_id,
        node_id=node_id,
        choice_id=choice_id,
        timestamp=timestamp,
    )


def test_build_room_state_reconstructs_node_and_video_tallies():
    decisions = [
        _decision(
            user_id="viewer-1",
            node_id="node-old",
            choice_id="choice-x",
            timestamp=2.0,
        ),
        _decision(user_id="viewer-2", choice_id="choice-a", timestamp=5.0),
        _decision(user_id="viewer-3", choice_id="choice-b", timestamp=8.0),
        _decision(
            user_id="viewer-4",
            video_id="video-2",
            node_id="other-poll",
            choice_id="other-choice",
        ),
    ]
    server_timestamp = datetime(2026, 11, 23, tzinfo=timezone.utc)

    snapshot = build_room_state(
        room_id="room-1",
        session_id="session-1",
        video_id="video-1",
        segment_id="segment-2",
        anchor_timestamp=12.5,
        server_timestamp=server_timestamp,
        playback_state="playing",
        active_cue_id="cue-1",
        participant_count=2,
        decisions=decisions,
    )

    assert snapshot.type == "room:state"
    assert snapshot.version == 1
    assert snapshot.payload.active_node_id == "poll-1"
    assert snapshot.payload.anchor_timestamp == 12.5
    assert snapshot.payload.server_timestamp == server_timestamp
    assert snapshot.payload.decision_tallies == {
        "node-old": {"choice-x": 1},
        "poll-1": {"choice-a": 1, "choice-b": 1},
    }
    assert snapshot.payload.total_decisions == 3
    assert snapshot.payload.participant_count == 2


def test_live_event_union_validates_discriminator_and_version():
    event = TypeAdapter(LiveSessionEvent).validate_python(
        {
            "type": "playback:sync",
            "payload": {
                "room_id": "room-1",
                "video_id": "video-1",
                "anchor_timestamp": 7.0,
                "server_timestamp": "2026-11-23T00:00:00Z",
                "playback_state": "paused",
            },
        }
    )

    assert event.type == "playback:sync"
    assert event.version == 1


def test_aggregate_decision_tallies_can_filter_video():
    decisions = [
        _decision(user_id="viewer-1"),
        _decision(user_id="viewer-2", video_id="video-2"),
    ]

    assert aggregate_decision_tallies(decisions, video_id="video-1") == {
        "poll-1": {"choice-a": 1}
    }


@pytest.mark.asyncio
async def test_handle_decision_submitted_persists_and_builds_room_updates(async_db_session):
    repository = SQLAlchemySessionRepository(async_db_session)
    previous_decisions = [
        _decision(user_id="viewer-1", choice_id="choice-a", timestamp=3.0),
        _decision(user_id="viewer-2", choice_id="choice-b", timestamp=4.0),
        _decision(user_id="viewer-3", video_id="video-2"),
    ]
    submission = _decision(
        user_id="viewer-4",
        choice_id="choice-a",
        timestamp=9.0,
    )
    event = DecisionSubmittedEvent(
        payload=DecisionSubmittedPayload(room_id="room-1", decision=submission)
    )

    updates = await handle_decision_submitted(
        event,
        repository,
        previous_decisions=previous_decisions,
    )

    assert updates.poll_tally.payload.choice_counts == {
        "choice-a": 2,
        "choice-b": 1,
    }
    assert updates.poll_tally.payload.total_submissions == 3
    assert updates.analytics_updated.payload.total_decisions == 3
    assert updates.analytics_updated.payload.decision_tallies == {
        "poll-1": {"choice-a": 2, "choice-b": 1}
    }

    restored = await repository.get_session_state("viewer-4", "session-viewer-4")
    assert restored is not None
    assert restored.decision_history == [submission]
