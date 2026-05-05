"""
Project state management — simple, file-based, stateless.

All state lives in the user's workspace under aidlc-docs/{project-name}/.
The server reads/writes JSON and markdown files. No in-memory state survives restarts.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .validation import ensure_within, validate_content_size, validate_name

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


VALID_MODES = frozenset({"suggest", "human_in_loop", "autonomous"})


class Project:
    """Manages a single AIDLC project's state on disk."""

    def __init__(self, workspace: Path, name: str):
        self.workspace = Path(workspace).resolve()
        self.name = validate_name(name, "project name")
        self.root = ensure_within(
            self.workspace / "aidlc-docs" / self.name, self.workspace
        )

    @property
    def state_file(self) -> Path:
        return self.root / "project.json"

    @property
    def aidlc_state_file(self) -> Path:
        return self.root / "aidlc-state.md"

    @property
    def audit_file(self) -> Path:
        return self.root / "audit.md"

    def exists(self) -> bool:
        return self.state_file.is_file()

    def load_state(self) -> dict[str, Any]:
        """Load project state from disk."""
        if not self.state_file.is_file():
            raise FileNotFoundError(f"Project not found: {self.name}")
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def save_state(self, state: dict[str, Any]) -> None:
        """Save project state to disk atomically."""
        to_write = {**state, "updated_at": _now()}
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(to_write, indent=2, default=str), encoding="utf-8"
        )
        tmp.replace(self.state_file)

    def create(self, user_request: str, operational_mode: str) -> dict[str, Any]:
        """Create a new project with initial directory structure."""
        if operational_mode not in VALID_MODES:
            raise ValueError(f"Invalid operational mode: {operational_mode}")
        if self.exists():
            raise FileExistsError(f"Project already exists: {self.name}")

        now = _now()
        state = {
            "name": self.name,
            "user_request": user_request,
            "operational_mode": operational_mode,
            "current_phase": "inception",
            "current_stage": "workspace-detection",
            "phase_state": "not_started",
            "created_at": now,
            "updated_at": now,
            "completed_stages": [],
            "skipped_stages": [],
        }

        # Create directory structure matching core-workflow.md spec
        dirs = [
            self.root / "inception" / "plans",
            self.root / "inception" / "requirements",
            self.root / "inception" / "user-stories",
            self.root / "inception" / "application-design",
            self.root / "construction" / "plans",
            self.root / "construction" / "build-and-test",
            self.root / "operations",
            self.root / "audit",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        self.save_state(state)
        self._write_aidlc_state(state, user_request)
        self._write_audit_entry("project_created", {
            "project": self.name,
            "mode": operational_mode,
            "request": user_request,
        })

        return state

    def update_stage(
        self, phase: str, stage: str, phase_state: str = "in_progress"
    ) -> dict[str, Any]:
        """Update current stage in project state."""
        state = self.load_state()
        state["current_phase"] = phase
        state["current_stage"] = stage
        state["phase_state"] = phase_state
        self.save_state(state)
        return state

    def complete_stage(self, stage: str) -> dict[str, Any]:
        """Mark a stage as completed."""
        state = self.load_state()
        if stage not in state.get("completed_stages", []):
            state.setdefault("completed_stages", []).append(stage)
        state["phase_state"] = "completed"
        self.save_state(state)
        self._write_audit_entry("stage_completed", {"stage": stage})
        return state

    def skip_stage(self, stage: str, reason: str) -> dict[str, Any]:
        """Mark a stage as skipped."""
        state = self.load_state()
        if stage not in state.get("skipped_stages", []):
            state.setdefault("skipped_stages", []).append(stage)
        self.save_state(state)
        self._write_audit_entry("stage_skipped", {"stage": stage, "reason": reason})
        return state

    def save_deliverable(self, phase: str, stage: str, content: str) -> Path:
        """Save a stage deliverable to the appropriate directory."""
        validate_name(phase, "phase")
        validate_name(stage, "stage")
        validate_content_size(content, "deliverable")
        deliverable_dir = ensure_within(self.root / phase / stage, self.root)
        deliverable_dir.mkdir(parents=True, exist_ok=True)
        deliverable_path = deliverable_dir / f"{stage}.md"
        deliverable_path.write_text(content, encoding="utf-8")
        return deliverable_path

    def append_audit(self, action: str, details: str) -> None:
        """Append a raw entry to the audit log."""
        self._write_audit_entry(action, {"details": details})

    def _write_audit_entry(self, action: str, data: dict[str, Any]) -> None:
        """Append structured entry to audit.md."""
        now = _now()
        entry = f"\n## {action}\n**Timestamp**: {now}\n"
        for k, v in data.items():
            entry += f"**{k.title()}**: {v}\n"
        entry += "\n---\n"

        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not self.audit_file.exists() or self.audit_file.stat().st_size == 0
        with open(self.audit_file, "a", encoding="utf-8") as f:
            if needs_header:
                f.write("# AIDLC Audit Log\n\n")
            f.write(entry)

    def _write_aidlc_state(self, state: dict[str, Any], description: str) -> None:
        """Write the human-readable aidlc-state.md file."""
        content = f"""# AIDLC Project State

## Project Information
- **Name**: {state['name']}
- **Mode**: {state['operational_mode']}
- **Created**: {state['created_at']}

## Current Status
- **Phase**: {state['current_phase']}
- **Stage**: {state['current_stage']}
- **Last Updated**: {state['updated_at']}

## Project Description
{description}

## Workflow Progress
- [ ] Inception Phase
  - [ ] Workspace Detection
  - [ ] Reverse Engineering (conditional)
  - [ ] Requirements Analysis
  - [ ] User Stories (conditional)
  - [ ] Workflow Planning
  - [ ] Application Design (conditional)
  - [ ] Units Generation (conditional)
- [ ] Construction Phase
  - [ ] Functional Design (conditional, per-unit)
  - [ ] NFR Requirements (conditional, per-unit)
  - [ ] NFR Design (conditional, per-unit)
  - [ ] Infrastructure Design (conditional, per-unit)
  - [ ] Code Generation (per-unit)
  - [ ] Build and Test
- [ ] Operations Phase (placeholder)
"""
        self.aidlc_state_file.write_text(content, encoding="utf-8")


def list_projects(workspace: Path) -> list[dict[str, Any]]:
    """List all projects in a workspace."""
    docs_dir = Path(workspace) / "aidlc-docs"
    if not docs_dir.is_dir():
        return []

    projects = []
    for project_dir in sorted(docs_dir.iterdir()):
        state_file = project_dir / "project.json"
        if project_dir.is_dir() and state_file.is_file():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                projects.append(state)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Skipping corrupt project {project_dir.name}: {e}")
    return projects


def find_most_recent_project(workspace: Path) -> dict[str, Any] | None:
    """Find the most recently updated project."""
    projects = list_projects(workspace)
    if not projects:
        return None
    return max(projects, key=lambda p: p.get("updated_at", ""))
