from __future__ import annotations

import json

from backend.orchestrator.models import NextAction, TurnRecord, TurnRole
from backend.orchestrator.store import FileBackedSessionStore


def test_store_persists_session_and_step_artifacts(test_settings):
    store = FileBackedSessionStore(test_settings.data_root)
    session = store.create_session("Build a quarterly sales planning workflow.")

    user_turn = TurnRecord(role=TurnRole.USER, kind="problem_statement", content=session.problem_statement)
    session.conversation_history.append(user_turn)
    store.append_step_artifact(session, "user-message", {"turn": user_turn.model_dump(mode="json")})
    store.append_step_artifact(
        session,
        "state-check",
        {
            "state_check": {
                "needs_more_information": False,
                "next_action": NextAction.CREATE_PLAN.value,
                "confidence": 0.9,
            }
        },
    )
    store.append_markdown_artifact(
        session,
        "plan-v1",
        "# Example Plan\n\n## Goal\n\nShip it.",
        {"confidence": 0.91, "prompt_path": "prompts/orchestrator/plan-generation.md"},
    )
    store.save_session(session)

    loaded = store.load_session(session.session_id)
    assert loaded.session_id == session.session_id
    assert loaded.step_count == session.step_count

    session_path = test_settings.data_root / session.session_id / "session.json"
    steps_dir = test_settings.data_root / session.session_id / "steps"
    assert session_path.exists()
    assert (steps_dir / "001-user-message.json").exists()
    assert (steps_dir / "002-state-check.json").exists()
    assert (steps_dir / "003-plan-v1.md").read_text(encoding="utf-8").startswith("# Example Plan")
    metadata = json.loads((steps_dir / "004-plan-v1-metadata.json").read_text(encoding="utf-8"))
    assert metadata["payload"]["confidence"] == 0.91
