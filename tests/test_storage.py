import pytest
from interactive_video_backend_core.models import DecisionSubmission
from interactive_video_backend_core.storage_sqlalchemy import SQLAlchemySessionRepository

@pytest.mark.asyncio
async def test_save_and_retrieve_session_state(async_db_session):
    repo = SQLAlchemySessionRepository(async_db_session)
    
    # 1. Create a decision submission
    decision = DecisionSubmission(
        user_id="user_123",
        session_id="session_abc",
        video_id="vid_99",
        node_id="checkpoint_1",
        choice_id="path_a",
        timestamp=12.5,
        metadata={"score": 100}
    )
    
    # 2. Save it
    await repo.save_decision(decision)
    
    # 3. Retrieve session state
    state = await repo.get_session_state("user_123", "session_abc")
    
    assert state is not None
    assert state.user_id == "user_123"
    assert state.last_node_id == "checkpoint_1"
    assert state.last_timestamp == 12.5
    assert len(state.decision_history) == 1
    assert state.decision_history[0].choice_id == "path_a"