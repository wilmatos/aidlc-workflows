"""
AIDLC MCP Server — dynamically loads workflow guidance from aidlc-rules/.

Tools:
  1. aidlc_start_project     — Create a new project
  2. aidlc_get_guidance       — Get workflow/stage guidance (the core tool)
  3. aidlc_complete_stage     — Mark stage done, save deliverable, advance
  4. aidlc_list_projects      — List projects in workspace
  5. aidlc_log                — Append to audit log
  6. aidlc_manage_extensions  — List/read workflow extensions

Resources:
  - aidlc://workflow/core     — The core workflow (always-available)
"""

import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .__version__ import __version__
from .project import Project, find_most_recent_project, list_projects
from .validation import validate_content_size, validate_name, validate_workspace
from .workflow_loader import WorkflowLoader

logger = logging.getLogger(__name__)


PHASES: dict[str, list[str]] = {
    "inception": [
        "workspace-detection",
        "reverse-engineering",
        "requirements-analysis",
        "user-stories",
        "workflow-planning",
        "application-design",
        "units-generation",
    ],
    "construction": [
        "functional-design",
        "nfr-requirements",
        "nfr-design",
        "infrastructure-design",
        "code-generation",
        "build-and-test",
    ],
    "operations": [
        "operations",
    ],
}

PHASE_ORDER = ["inception", "construction", "operations"]
VALID_MODES = {"suggest", "human_in_loop", "autonomous"}


def _next_stage(phase: str, stage: str) -> dict[str, str | None]:
    """Determine the next stage/phase after completing a given stage."""
    stages = PHASES.get(phase, [])
    try:
        idx = stages.index(stage)
    except ValueError:
        return {"phase": phase, "stage": None, "status": "unknown_stage"}

    if idx + 1 < len(stages):
        return {"phase": phase, "stage": stages[idx + 1], "status": "next_stage"}

    phase_idx = PHASE_ORDER.index(phase)
    if phase_idx + 1 < len(PHASE_ORDER):
        next_phase = PHASE_ORDER[phase_idx + 1]
        return {"phase": next_phase, "stage": PHASES[next_phase][0], "status": "next_phase"}

    return {"phase": phase, "stage": None, "status": "workflow_complete"}


def create_server(
    workflow_dir: Path | None = None,
    extra_extension_dirs: list[Path] | None = None,
) -> FastMCP:
    """Create and configure the FastMCP server with all tools."""

    loader = WorkflowLoader(workflow_dir, extra_extension_dirs)
    loader.preload_extensions()

    mcp = FastMCP(
        name="AIDLC Workflow Server",
        version=__version__,
        instructions=(
            "AI Development Life Cycle workflow server. "
            "Guides LLM agents through a structured software development process "
            "defined in aidlc-rules/. Use aidlc_get_guidance to load stage-specific "
            "instructions. All project state lives in the user's workspace."
        ),
    )

    @mcp.resource("aidlc://workflow/core")
    def core_workflow_resource() -> str:
        """The core AIDLC workflow — always-available reference."""
        return loader.get_core_workflow()

    @mcp.tool()
    async def aidlc_start_project(
        name: str,
        user_request: str,
        workspace_path: str,
        operational_mode: str,
    ) -> dict[str, Any]:
        """Create a new AIDLC project.

        IMPORTANT: Before calling, ask the user which operational mode they want:
        'suggest' (recommended), 'human_in_loop', or 'autonomous'.

        Args:
            name: Project name (alphanumeric, hyphens, underscores)
            user_request: What the user wants to build
            workspace_path: Absolute path to the workspace directory
            operational_mode: 'suggest', 'human_in_loop', or 'autonomous'
        """
        if operational_mode not in VALID_MODES:
            return {
                "success": False,
                "error": f"Invalid mode '{operational_mode}'. "
                         f"Must be one of: {', '.join(sorted(VALID_MODES))}",
            }

        try:
            validate_name(name, "project name")
            ws = validate_workspace(workspace_path)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        project = Project(ws, name)
        if project.exists():
            return {"success": False, "error": f"Project '{name}' already exists."}

        try:
            state = project.create(user_request, operational_mode)
        except Exception as e:
            return {"success": False, "error": str(e)}

        welcome = ""
        try:
            welcome = loader.get_detail("common", "welcome-message")
        except FileNotFoundError:
            pass

        return {
            "success": True,
            "project": state,
            "welcome_message": welcome,
            "next_action": (
                "Call aidlc_get_guidance with guidance_type='stage', "
                "phase='inception', stage='workspace-detection' to begin."
            ),
        }

    @mcp.tool()
    async def aidlc_get_guidance(
        guidance_type: str,
        workspace_path: str | None = None,
        project_id: str | None = None,
        phase: str | None = None,
        stage: str | None = None,
        detail_name: str | None = None,
    ) -> dict[str, Any]:
        """Load workflow guidance dynamically from aidlc-rules/.

        This is the primary tool. Workflow files can be edited at any time
        and changes take effect immediately (no restart needed).

        Args:
            guidance_type: What to load. One of:
                'core_workflow' - Main workflow instructions
                'startup' - Common files needed at workflow start
                'stage' - Stage-specific guidance (requires phase + stage)
                'detail' - A specific detail file (requires detail_name)
                'project_status' - Current project state
            workspace_path: Workspace path (for project_status)
            project_id: Project name (for project_status and stage tracking)
            phase: Phase name for stage guidance
            stage: Stage name (e.g. 'requirements-analysis')
            detail_name: For 'detail' type, format: 'category/name'
        """
        try:
            if guidance_type == "core_workflow":
                return {
                    "success": True,
                    "content": loader.get_core_workflow(),
                    "note": "Keep this in context throughout the workflow.",
                }

            if guidance_type == "startup":
                common = loader.get_common_startup_guidance()
                return {
                    "success": True,
                    "files_loaded": list(common.keys()),
                    "content": common,
                    "note": "Keep these in context until workflow ends.",
                }

            if guidance_type == "stage":
                if not phase or not stage:
                    return {
                        "success": False,
                        "error": "phase and stage required for 'stage' guidance.",
                    }
                if phase not in PHASES:
                    return {"success": False, "error": f"Unknown phase: {phase}"}
                if stage not in PHASES[phase]:
                    return {
                        "success": False,
                        "error": f"Unknown stage '{stage}' for phase '{phase}'.",
                    }
                guidance = loader.get_stage_guidance(phase, stage)
                if workspace_path and project_id:
                    try:
                        ws = validate_workspace(workspace_path)
                        proj = Project(ws, project_id)
                        proj.update_stage(phase, stage, "in_progress")
                        proj.append_audit("stage_started", f"Started {phase}/{stage}")
                    except Exception as e:
                        logger.warning(f"Could not update project state: {e}")
                return {
                    "success": True,
                    "phase": phase,
                    "stage": stage,
                    "content": guidance,
                    "note": f"Follow stage_detail instructions. Unload after {stage}.",
                }

            if guidance_type == "detail":
                if not detail_name or "/" not in detail_name:
                    return {
                        "success": False,
                        "error": "detail_name required as 'category/name'.",
                    }
                cat, name = detail_name.split("/", 1)
                content = loader.get_detail(cat, name)
                return {"success": True, "detail": detail_name, "content": content}

            if guidance_type == "project_status":
                if not workspace_path:
                    return {"success": False, "error": "workspace_path required."}
                ws = validate_workspace(workspace_path)
                if project_id:
                    proj = Project(ws, project_id)
                    if not proj.exists():
                        return {"success": False, "error": f"Project '{project_id}' not found."}
                    return {"success": True, "project": proj.load_state()}
                state = find_most_recent_project(ws)
                if not state:
                    return {"success": False, "error": "No projects found."}
                return {"success": True, "project": state}

            return {"success": False, "error": f"Unknown guidance_type: {guidance_type}"}

        except FileNotFoundError as e:
            filename = e.filename or 'unknown'
            return {"success": False, "error": f"Requested file not found: {filename}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception:
            logger.exception("Error in aidlc_get_guidance")
            return {"success": False, "error": "An internal error occurred."}

    @mcp.tool()
    async def aidlc_complete_stage(
        workspace_path: str,
        project_id: str,
        stage: str,
        content: str = "",
        skip: bool = False,
        skip_reason: str = "",
    ) -> dict[str, Any]:
        """Complete a workflow stage, save its deliverable, and advance.

        Args:
            workspace_path: Absolute path to workspace
            project_id: Project name
            stage: Stage being completed (e.g. 'requirements-analysis')
            content: The deliverable content (markdown)
            skip: If True, skip this stage instead of completing it
            skip_reason: Reason for skipping (required if skip=True)
        """
        try:
            ws = validate_workspace(workspace_path)
            validate_name(project_id, "project name")
            validate_name(stage, "stage")
            if not skip:
                validate_content_size(content, "deliverable")
        except ValueError as e:
            return {"success": False, "error": str(e)}

        project = Project(ws, project_id)
        if not project.exists():
            return {"success": False, "error": f"Project '{project_id}' not found."}

        try:
            state = project.load_state()
            phase = state["current_phase"]

            if skip:
                project.skip_stage(stage, skip_reason or "Skipped by assessment")
            else:
                project.save_deliverable(phase, stage, content)
                project.complete_stage(stage)

            next_info = _next_stage(phase, stage)
            if next_info["stage"]:
                next_phase = next_info["phase"]
                next_stage = next_info["stage"]
                assert isinstance(next_phase, str) and isinstance(next_stage, str)
                project.update_stage(next_phase, next_stage, "not_started")

            return {
                "success": True,
                "completed_stage": stage,
                "skipped": skip,
                "next": next_info,
                "project": project.load_state(),
                "next_action": (
                    f"Call aidlc_get_guidance with phase='{next_info['phase']}', "
                    f"stage='{next_info['stage']}' to continue."
                    if next_info["stage"]
                    else "Workflow complete."
                ),
            }
        except Exception as e:
            logger.exception("Error completing stage")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def aidlc_list_projects(workspace_path: str) -> dict[str, Any]:
        """List all AIDLC projects in the workspace.

        Args:
            workspace_path: Absolute path to workspace directory
        """
        try:
            projects = list_projects(validate_workspace(workspace_path))
            return {"success": True, "count": len(projects), "projects": projects}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def aidlc_log(
        workspace_path: str,
        project_id: str,
        action: str,
        details: str,
    ) -> dict[str, Any]:
        """Append an entry to the project's audit log.

        Per AIDLC rules, ALL user inputs and actions must be logged with
        complete raw input — never summarize.

        Args:
            workspace_path: Absolute path to workspace
            project_id: Project name
            action: Action type (e.g. 'user_input', 'approval', 'decision')
            details: Complete details to log
        """
        project = Project(validate_workspace(workspace_path), project_id)
        if not project.exists():
            return {"success": False, "error": f"Project '{project_id}' not found."}
        try:
            project.append_audit(action, details)
            return {"success": True, "message": f"Logged: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def aidlc_manage_extensions(
        action: str = "list",
        extension_name: str | None = None,
    ) -> dict[str, Any]:
        """Manage workflow extensions.

        Extensions in aidlc-rules/aidlc-rules/aws-aidlc-rule-details/extensions/ provide domain-specific
        guidance (e.g. 'react-frontend', 'aws-infrastructure').

        Args:
            action: 'list' to see available extensions, 'read' to load one
            extension_name: Name of extension to read (without .md)
        """
        try:
            if action == "list":
                return {"success": True, "extensions": loader.list_extensions()}
            if action == "read":
                if not extension_name:
                    return {"success": False, "error": "extension_name required."}
                content = loader.get_extension(extension_name)
                return {"success": True, "name": extension_name, "content": content}
            return {"success": False, "error": f"Unknown action: {action}"}
        except FileNotFoundError:
            return {"success": False, "error": f"Extension '{extension_name}' not found."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return mcp
