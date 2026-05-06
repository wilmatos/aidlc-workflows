# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Entry point for AIDLC MCP Server."""

import argparse
import asyncio
import logging
import sys

from .__version__ import __version__, get_rules_version
from .server import create_server


def _version_string() -> str:
    """Build a version string including rules provenance."""
    parts = [f"aidlc-mcp-server {__version__}"]
    meta = get_rules_version()
    if meta:
        ref = meta.get("ref", "unknown")
        commit = meta.get("commit", "unknown")[:12]
        parts.append(f"  rules: {ref} ({commit})")
    return "\n".join(parts)


def main() -> None:
    """Run the AIDLC MCP Server."""
    parser = argparse.ArgumentParser(
        description="AIDLC MCP Server — AI Development Life Cycle workflow guidance",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
    )
    parser.add_argument(
        "--workflow-dir",
        type=str,
        default=None,
        help="Path to rules directory (auto-detected if omitted)",
    )
    parser.add_argument(
        "--extension-dirs",
        type=str,
        default=None,
        help=(
            "Additional extension directories, colon-separated. "
            "Also configurable via AIDLC_EXTENSION_DIRS env var."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    from pathlib import Path

    workflow_dir = Path(args.workflow_dir) if args.workflow_dir else None
    extra_extension_dirs = None
    if args.extension_dirs:
        import os
        extra_extension_dirs = [
            Path(p) for p in args.extension_dirs.split(os.pathsep) if p.strip()
        ]

    try:
        mcp = create_server(workflow_dir, extra_extension_dirs)
        asyncio.run(mcp.run_async())
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
