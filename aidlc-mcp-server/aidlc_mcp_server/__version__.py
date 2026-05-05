"""Version information for AIDLC MCP Server."""

from pathlib import Path

__version__ = "0.1.0"


def get_rules_version() -> dict[str, str]:
    """Read aidlc-rules provenance from .sync-metadata.

    Returns a dict with keys: source_repo, ref, commit, synced_at.
    Returns empty dict if metadata file is not found.
    """
    candidates = [
        Path(__file__).parent / "aidlc-rules" / ".sync-metadata",
        Path(__file__).parent.parent / "aidlc-rules" / ".sync-metadata",
        Path.cwd() / "aidlc-rules" / ".sync-metadata",
    ]
    for path in candidates:
        if path.is_file():
            meta: dict[str, str] = {}
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    meta[key.strip()] = value.strip()
            return meta
    return {}
