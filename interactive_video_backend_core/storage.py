from abc import ABC, abstractmethod
from typing import List, Optional
from interactive_video_backend_core.models import DecisionSubmission, SessionResumeResponse

class AbstractSessionRepository(ABC):
    """Abstract storage interface. Host frameworks implement this using their own DB session."""

    @abstractmethod
    async def save_decision(self, decision: DecisionSubmission) -> None:
        """Persists a new decision to the ledger."""
        pass

    @abstractmethod
    async def get_session_state(self, user_id: str, session_id: str) -> Optional[SessionResumeResponse]:
        """Retrieves the full decision ledger and latest state for multi-device resume."""
        pass