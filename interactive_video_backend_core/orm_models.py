from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DecisionModel(Base):
    __tablename__ = "ivl_decision_ledger"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    video_id: Mapped[str] = mapped_column(String)
    node_id: Mapped[str] = mapped_column(String)
    choice_id: Mapped[str] = mapped_column(String)
    timestamp: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
