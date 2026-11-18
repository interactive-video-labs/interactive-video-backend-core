from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class DecisionSubmission(BaseModel):
    user_id: str
    session_id: str
    video_id: str
    node_id: str
    choice_id: str
    timestamp: float = Field(..., description="Playback timestamp in seconds")
    metadata: Optional[Dict[str, Any]] = None

class SessionResumeResponse(BaseModel):
    user_id: str
    session_id: str
    video_id: str
    last_node_id: str
    last_timestamp: float
    decision_history: list[DecisionSubmission] = []
    updated_at: datetime