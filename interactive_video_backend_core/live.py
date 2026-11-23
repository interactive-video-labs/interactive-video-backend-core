from collections import defaultdict
from datetime import datetime, timezone
from typing import Annotated, Literal, Sequence, Union

from pydantic import BaseModel, Field

from interactive_video_backend_core.logic import DecisionLedgerEngine
from interactive_video_backend_core.models import DecisionSubmission
from interactive_video_backend_core.storage import AbstractSessionRepository

PlaybackState = Literal["playing", "paused", "ended"]
PresenceState = Literal["joined", "left"]


class RoomStatePayload(BaseModel):
    room_id: str
    session_id: str
    video_id: str
    segment_id: str | None = None
    anchor_timestamp: float = Field(ge=0, description="Playback position in seconds")
    server_timestamp: datetime
    playback_state: PlaybackState
    active_cue_id: str | None = None
    active_node_id: str | None = None
    participant_count: int = Field(ge=0)
    total_decisions: int = Field(ge=0)
    decision_tallies: dict[str, dict[str, int]] = Field(default_factory=dict)


class RoomStateEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["room:state"] = "room:state"
    payload: RoomStatePayload


class PlaybackSyncPayload(BaseModel):
    room_id: str
    video_id: str
    segment_id: str | None = None
    anchor_timestamp: float = Field(ge=0, description="Playback position in seconds")
    server_timestamp: datetime
    playback_state: PlaybackState


class PlaybackSyncEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["playback:sync"] = "playback:sync"
    payload: PlaybackSyncPayload


class CueTriggeredPayload(BaseModel):
    room_id: str
    video_id: str
    cue_id: str
    playback_timestamp: float = Field(ge=0)


class CueTriggeredEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["cue:triggered"] = "cue:triggered"
    payload: CueTriggeredPayload


class NodeEnteredPayload(BaseModel):
    room_id: str
    video_id: str
    node_id: str
    playback_timestamp: float = Field(ge=0)


class NodeEnteredEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["node:entered"] = "node:entered"
    payload: NodeEnteredPayload


class DecisionSubmittedPayload(BaseModel):
    room_id: str
    decision: DecisionSubmission


class DecisionSubmittedEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["decision:submitted"] = "decision:submitted"
    payload: DecisionSubmittedPayload


class PollTallyPayload(BaseModel):
    room_id: str
    video_id: str
    node_id: str
    choice_counts: dict[str, int] = Field(default_factory=dict)
    total_submissions: int = Field(ge=0)


class PollTallyEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["poll:tally"] = "poll:tally"
    payload: PollTallyPayload


class AnalyticsUpdatedPayload(BaseModel):
    room_id: str
    video_id: str
    total_decisions: int = Field(ge=0)
    decision_tallies: dict[str, dict[str, int]] = Field(default_factory=dict)


class AnalyticsUpdatedEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["analytics:updated"] = "analytics:updated"
    payload: AnalyticsUpdatedPayload


class PresenceUpdatePayload(BaseModel):
    room_id: str
    user_id: str
    state: PresenceState
    participant_count: int = Field(ge=0)


class PresenceUpdateEvent(BaseModel):
    version: Literal[1] = 1
    type: Literal["presence:update"] = "presence:update"
    payload: PresenceUpdatePayload


class DecisionUpdateEvents(BaseModel):
    poll_tally: PollTallyEvent
    analytics_updated: AnalyticsUpdatedEvent


LiveSessionEvent = Annotated[
    Union[
        RoomStateEvent,
        PlaybackSyncEvent,
        CueTriggeredEvent,
        NodeEnteredEvent,
        DecisionSubmittedEvent,
        PollTallyEvent,
        AnalyticsUpdatedEvent,
        PresenceUpdateEvent,
    ],
    Field(discriminator="type"),
]


def aggregate_decision_tallies(
    decisions: Sequence[DecisionSubmission],
    *,
    video_id: str | None = None,
) -> dict[str, dict[str, int]]:
    """Count choices by node, optionally restricting results to one video."""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for decision in decisions:
        if video_id is not None and decision.video_id != video_id:
            continue
        counts[decision.node_id][decision.choice_id] += 1
    return {node_id: dict(choice_counts) for node_id, choice_counts in counts.items()}


def build_room_state(
    *,
    room_id: str,
    session_id: str,
    video_id: str,
    anchor_timestamp: float,
    playback_state: PlaybackState,
    participant_count: int,
    decisions: Sequence[DecisionSubmission] = (),
    server_timestamp: datetime | None = None,
    segment_id: str | None = None,
    active_cue_id: str | None = None,
    active_node_id: str | None = None,
) -> RoomStateEvent:
    """Build a reconnect snapshot from current playback and room ledger state."""
    video_decisions = [decision for decision in decisions if decision.video_id == video_id]
    decision_tallies = aggregate_decision_tallies(video_decisions)
    if active_node_id is None and video_decisions:
        active_node_id, _ = DecisionLedgerEngine.reconstruct_state(video_decisions)

    return RoomStateEvent(
        payload=RoomStatePayload(
            room_id=room_id,
            session_id=session_id,
            video_id=video_id,
            segment_id=segment_id,
            anchor_timestamp=anchor_timestamp,
            server_timestamp=server_timestamp or datetime.now(timezone.utc),
            playback_state=playback_state,
            active_cue_id=active_cue_id,
            active_node_id=active_node_id,
            participant_count=participant_count,
            total_decisions=sum(sum(choices.values()) for choices in decision_tallies.values()),
            decision_tallies=decision_tallies,
        )
    )


def build_poll_tally(
    *,
    room_id: str,
    video_id: str,
    node_id: str,
    decisions: Sequence[DecisionSubmission],
) -> PollTallyEvent:
    """Build the aggregate choice counts for one room poll or branch node."""
    choice_counts: dict[str, int] = defaultdict(int)
    for decision in decisions:
        if decision.video_id == video_id and decision.node_id == node_id:
            choice_counts[decision.choice_id] += 1

    counts = dict(choice_counts)
    return PollTallyEvent(
        payload=PollTallyPayload(
            room_id=room_id,
            video_id=video_id,
            node_id=node_id,
            choice_counts=counts,
            total_submissions=sum(counts.values()),
        )
    )


async def handle_decision_submitted(
    event: DecisionSubmittedEvent,
    repository: AbstractSessionRepository,
    *,
    previous_decisions: Sequence[DecisionSubmission] = (),
) -> DecisionUpdateEvents:
    """Persist a submission, then build broadcast events from the room ledger.

    ``previous_decisions`` must contain the relevant room's existing decisions
    for this video and must not already include the submitted decision.
    """
    decision = event.payload.decision
    await repository.save_decision(decision)

    room_decisions = [
        prior for prior in previous_decisions if prior.video_id == decision.video_id
    ]
    current_decisions = [*room_decisions, decision]
    return DecisionUpdateEvents(
        poll_tally=build_poll_tally(
            room_id=event.payload.room_id,
            video_id=decision.video_id,
            node_id=decision.node_id,
            decisions=current_decisions,
        ),
        analytics_updated=AnalyticsUpdatedEvent(
            payload=AnalyticsUpdatedPayload(
                room_id=event.payload.room_id,
                video_id=decision.video_id,
                total_decisions=len(current_decisions),
                decision_tallies=aggregate_decision_tallies(current_decisions),
            )
        ),
    )
