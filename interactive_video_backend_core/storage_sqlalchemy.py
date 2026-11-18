from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from interactive_video_backend_core.storage import AbstractSessionRepository
from interactive_video_backend_core.models import DecisionSubmission, SessionResumeResponse
from interactive_video_backend_core.orm_models import DecisionModel
from interactive_video_backend_core.logic import DecisionLedgerEngine

class SQLAlchemySessionRepository(AbstractSessionRepository):
    """SQLAlchemy implementation of the session and decision storage layer."""

    def __init__(self, session: AsyncSession):
        self.db = session

    async def save_decision(self, decision: DecisionSubmission) -> None:
        """Persists a new decision entry into the database ledger."""
        import uuid
        db_decision = DecisionModel(
            id=str(uuid.uuid4()),
            user_id=decision.user_id,
            session_id=decision.session_id,
            video_id=decision.video_id,
            node_id=decision.node_id,
            choice_id=decision.choice_id,
            timestamp=decision.timestamp,
            metadata_json=decision.metadata
        )
        self.db.add(db_decision)
        await self.db.commit()

    async def get_session_state(self, user_id: str, session_id: str) -> Optional[SessionResumeResponse]:
        """Queries the decision ledger and reconstructs the latest state for multi-device resume."""
        stmt = (
            select(DecisionModel)
            .where(DecisionModel.user_id == user_id)
            .where(DecisionModel.session_id == session_id)
            .order_by(DecisionModel.timestamp.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            return None

        # Convert ORM rows back to core Pydantic DecisionSubmission models
        decisions = [
            DecisionSubmission(
                user_id=row.user_id,
                session_id=row.session_id,
                video_id=row.video_id,
                node_id=row.node_id,
                choice_id=row.choice_id,
                timestamp=row.timestamp,
                metadata=row.metadata_json
            )
            for row in rows
        ]

        # Use pure core logic to compute the current playback state
        last_node_id, last_timestamp = DecisionLedgerEngine.reconstruct_state(decisions)

        return SessionResumeResponse(
            user_id=user_id,
            session_id=session_id,
            video_id=rows[-1].video_id,
            last_node_id=last_node_id,
            last_timestamp=last_timestamp,
            decision_history=decisions,
            updated_at=rows[-1].created_at
        )