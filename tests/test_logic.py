import pytest
from interactive_video_backend_core.models import DecisionSubmission
from interactive_video_backend_core.logic import DecisionLedgerEngine

def test_validate_transition_success():
    allowed = ["opt_a", "opt_b"]
    assert DecisionLedgerEngine.validate_transition("node_1", "opt_a", allowed) is True

def test_validate_transition_failure():
    allowed = ["opt_a", "opt_b"]
    with pytest.raises(ValueError, match="Invalid choice"):
        DecisionLedgerEngine.validate_transition("node_1", "opt_c", allowed)

def test_reconstruct_state_orders_chronologically():
    # Out of order submissions
    decisions = [
        DecisionSubmission(user_id="u1", session_id="s1", video_id="v1", node_id="node_2", choice_id="b", timestamp=15.0),
        DecisionSubmission(user_id="u1", session_id="s1", video_id="v1", node_id="node_1", choice_id="a", timestamp=5.0),
    ]
    
    last_node, last_time = DecisionLedgerEngine.reconstruct_state(decisions)
    
    # Should pick the latest timestamp (node_2 at 15.0)
    assert last_node == "node_2"
    assert last_time == 15.0