from datetime import datetime, timezone
from sqlalchemy import Column, Float, String, JSON, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DecisionModel(Base):
    __tablename__ = "ivl_decision_ledger"

    id = Column(String, primary_key=True)  # e.g., uuid or composite
    user_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    video_id = Column(String, nullable=False)
    node_id = Column(String, nullable=False)
    choice_id = Column(String, nullable=False)
    timestamp = Column(Float, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    
    # Use a lambda with timezone-aware UTC datetime
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
