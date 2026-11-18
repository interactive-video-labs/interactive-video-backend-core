from typing import List
from interactive_video_backend_core.models import DecisionSubmission

class DecisionLedgerEngine:
    """Pure business logic engine for interactive video decision flows."""
    
    @staticmethod
    def validate_transition(current_node: str, choice_id: str, allowed_choices: List[str]) -> bool:
        """Ensures the submitted choice is a valid branch path."""
        if choice_id not in allowed_choices:
            raise ValueError(f"Invalid choice '{choice_id}' for node '{current_node}'.")
        return True

    @staticmethod
    def reconstruct_state(decisions: List[DecisionSubmission]) -> tuple[str, float]:
        """Reconstructs the last known valid state from a time-ordered ledger."""
        if not decisions:
            return "start", 0.0
        
        # Sort chronologically just in case
        sorted_decisions = sorted(decisions, key=lambda d: d.timestamp)
        latest = sorted_decisions[-1]
        
        return latest.node_id, latest.timestamp