# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Input validation and path safety utilities.

Single point of enforcement for all user-supplied values that touch the filesystem.
"""

import re
from pathlib import Path

# Strict pattern for project names, stage names, extension names, detail names
_SAFE_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")

# Pattern for extension paths: slash-separated safe segments (e.g. "security/baseline/security-baseline")
_SAFE_SEGMENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")

VALID_CATEGORIES = frozenset({"common", "inception", "construction", "operations"})

MAX_DELIVERABLE_SIZE = 1_000_000  # 1 MB


def validate_name(value: str, label: str = "name") -> str:
    """Validate a path component (project name, stage name, etc.)."""
    if not _SAFE_NAME.match(value):
        raise ValueError(
            f"Invalid {label}: '{value}'. "
            "Must start with alphanumeric, contain only alphanumeric/hyphens/underscores, "
            "and be 1-100 characters."
        )
    return value


def validate_extension_path(value: str) -> str:
    """Validate an extension path (slash-separated safe segments).

    Accepts both flat names ('my-extension') and nested paths
    ('security/baseline/security-baseline').
    """
    if not value or not value.strip():
        raise ValueError("Extension path cannot be empty.")
    segments = value.split("/")
    if any(s == "" for s in segments):
        raise ValueError(
            f"Invalid extension path: '{value}'. Contains empty segments."
        )
    if ".." in segments:
        raise ValueError(
            f"Invalid extension path: '{value}'. Directory traversal not allowed."
        )
    for seg in segments:
        if not _SAFE_SEGMENT.match(seg):
            raise ValueError(
                f"Invalid extension path segment: '{seg}' in '{value}'. "
                "Each segment must start with alphanumeric, contain only "
                "alphanumeric/hyphens/underscores, and be 1-100 characters."
            )
    return value


def validate_category(category: str) -> str:
    """Validate a detail file category."""
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category: '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )
    return category


def validate_workspace(workspace_path: str) -> Path:
    """Validate workspace path is absolute and exists."""
    ws = Path(workspace_path).resolve()
    if not ws.is_absolute():
        raise ValueError(f"Workspace path must be absolute: {workspace_path}")
    if not ws.is_dir():
        raise ValueError(f"Workspace directory does not exist: {workspace_path}")
    return ws


def ensure_within(path: Path, boundary: Path) -> Path:
    """Ensure a resolved path stays within a boundary directory."""
    resolved = path.resolve()
    boundary_resolved = boundary.resolve()
    if not resolved.is_relative_to(boundary_resolved):
        raise ValueError("Path escapes allowed boundary.")
    return resolved


def validate_content_size(content: str, label: str = "content") -> str:
    """Validate content doesn't exceed size limits."""
    if len(content) > MAX_DELIVERABLE_SIZE:
        raise ValueError(
            f"{label} exceeds maximum size ({len(content)} > {MAX_DELIVERABLE_SIZE} bytes)."
        )
    return content
