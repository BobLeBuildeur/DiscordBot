from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from backend.orchestrator.models import SessionState, StepArtifact, utc_now


class FileBackedSessionStore:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self.data_root.mkdir(parents=True, exist_ok=True)

    def create_session(self, problem_statement: str) -> SessionState:
        session = SessionState(problem_statement=problem_statement)
        self._ensure_session_dirs(session.session_id)
        self.save_session(session)
        return session

    def load_session(self, session_id: str) -> SessionState:
        path = self.session_dir(session_id) / "session.json"
        if not path.exists():
            raise FileNotFoundError(f"Unknown session_id: {session_id}")
        return SessionState.model_validate_json(path.read_text(encoding="utf-8"))

    def save_session(self, session: SessionState) -> None:
        session.updated_at = utc_now()
        self._ensure_session_dirs(session.session_id)
        target = self.session_dir(session.session_id) / "session.json"
        self._atomic_write_text(
            target,
            json.dumps(session.model_dump(mode="json"), indent=2, sort_keys=True),
        )

    def append_step_artifact(
        self,
        session: SessionState,
        kind: str,
        payload: dict[str, Any],
    ) -> Path:
        artifact = StepArtifact(step_index=self._next_step_index(session), kind=kind, payload=payload)
        filename = f"{artifact.step_index:03d}-{kind}.json"
        target = self.steps_dir(session.session_id) / filename
        self._atomic_write_text(
            target,
            json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True),
        )
        return target

    def append_markdown_artifact(
        self,
        session: SessionState,
        kind: str,
        markdown: str,
        metadata: dict[str, Any],
    ) -> tuple[Path, Path]:
        markdown_index = self._next_step_index(session)
        markdown_target = self.steps_dir(session.session_id) / f"{markdown_index:03d}-{kind}.md"
        self._atomic_write_text(markdown_target, markdown)

        metadata_index = self._next_step_index(session)
        metadata_target = (
            self.steps_dir(session.session_id) / f"{metadata_index:03d}-{kind}-metadata.json"
        )
        artifact = StepArtifact(step_index=metadata_index, kind=f"{kind}-metadata", payload=metadata)
        self._atomic_write_text(
            metadata_target,
            json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True),
        )
        return markdown_target, metadata_target

    def session_dir(self, session_id: str) -> Path:
        return self.data_root / session_id

    def steps_dir(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "steps"

    def _ensure_session_dirs(self, session_id: str) -> None:
        self.steps_dir(session_id).mkdir(parents=True, exist_ok=True)

    def _next_step_index(self, session: SessionState) -> int:
        session.step_count += 1
        session.updated_at = utc_now()
        return session.step_count

    def _atomic_write_text(self, target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, target)
