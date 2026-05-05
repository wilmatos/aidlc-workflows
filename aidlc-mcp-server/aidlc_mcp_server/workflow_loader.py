"""
Dynamic workflow loader — reads all guidance from the aidlc-rules directory.

Rules are sourced from the monorepo root's aidlc-rules/ directory and copied
locally via scripts/sync-aidlc-rules.sh. In development, the loader also
checks the monorepo root directly.

Directory layout (relative to the rules root):
  aws-aidlc-rules/          — core workflow steering (core-workflow.md)
  aws-aidlc-rule-details/   — per-category detail files and extensions

Supports hot-reload: editing files in the rules dir automatically updates
the server's behavior without restart.
"""

import logging
import os
from pathlib import Path

from .validation import ensure_within, validate_category, validate_extension_path, validate_name

logger = logging.getLogger(__name__)


class WorkflowLoader:
    """Loads and caches workflow content from the aidlc-rules subtree."""

    def __init__(
        self,
        workflow_dir: Path | None = None,
        extra_extension_dirs: list[Path] | None = None,
    ):
        self._workflow_dir = workflow_dir or self._find_workflow_dir()
        self._extra_extension_dirs = self._resolve_extra_extension_dirs(
            extra_extension_dirs
        )
        self._cache: dict[str, tuple[str, float]] = {}  # path -> (content, mtime)
        logger.info(f"WorkflowLoader initialized: {self._workflow_dir}")
        if self._extra_extension_dirs:
            logger.info(
                f"Extra extension dirs: {self._extra_extension_dirs}"
            )

    @property
    def workflow_dir(self) -> Path:
        return self._workflow_dir

    @property
    def extra_extension_dirs(self) -> list[Path]:
        return list(self._extra_extension_dirs)

    def _resolve_extra_extension_dirs(
        self, dirs: list[Path] | None
    ) -> list[Path]:
        """Resolve extra extension dirs from args and AIDLC_EXTENSION_DIRS env var."""
        resolved: list[Path] = []

        # From env var (colon-separated paths)
        env_val = os.getenv("AIDLC_EXTENSION_DIRS", "")
        for raw in env_val.split(os.pathsep):
            p = raw.strip()
            if p:
                resolved.append(Path(p).resolve())

        # From explicit argument (takes precedence, appended after env)
        for d in (dirs or []):
            resolved.append(d.resolve())

        valid = []
        for d in resolved:
            if d.is_dir():
                valid.append(d)
            else:
                logger.warning(f"Extra extension dir not found, skipping: {d}")
        return valid

    def _find_workflow_dir(self) -> Path:
        """Find the aidlc-rules root directory.

        Resolution order:
        1. AIDLC_WORKFLOW_DIR env var (explicit override)
        2. Bundled inside the package (aidlc_mcp_server/aidlc-rules/) — for
           installed wheels / uvx
        3. Repo root relative to CWD or source tree — for local development

        Also supports the legacy subtree layout (aidlc-rules/aidlc-rules/)
        for backwards compatibility.
        """
        # Check AIDLC_WORKFLOW_DIR env var first (explicit override)
        env_dir = os.getenv("AIDLC_WORKFLOW_DIR")
        if env_dir:
            p = Path(env_dir)
            if p.is_dir():
                return p.resolve()

        # Check bundled rules inside the package (installed mode)
        bundled = Path(__file__).parent / "aidlc-rules"
        if (bundled / "aws-aidlc-rules").is_dir():
            return bundled.resolve()

        # Check repo root (development mode)
        roots = [Path.cwd(), Path(__file__).parent.parent]
        for root in roots:
            # New flat layout: aidlc-rules/aws-aidlc-rules/
            flat = root / "aidlc-rules"
            if (flat / "aws-aidlc-rules").is_dir():
                return flat.resolve()
            # Legacy subtree layout: aidlc-rules/aidlc-rules/
            nested = root / "aidlc-rules" / "aidlc-rules"
            if nested.is_dir():
                return nested.resolve()

        # Check monorepo root (one level above aidlc-mcp-server/)
        monorepo_root = Path(__file__).parent.parent.parent
        monorepo_rules = monorepo_root / "aidlc-rules"
        if (monorepo_rules / "aws-aidlc-rules").is_dir():
            return monorepo_rules.resolve()

        raise FileNotFoundError(
            "Cannot find aidlc-rules/ directory. "
            "Run scripts/sync-aidlc-rules.sh to copy rules from the monorepo root, "
            "or set AIDLC_WORKFLOW_DIR."
        )

    def _read_with_cache(self, path: Path) -> str:
        """Read file with mtime-based cache invalidation."""
        key = str(path)
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            self._cache.pop(key, None)
            raise

        cached = self._cache.get(key)
        if cached and cached[1] == mtime:
            return cached[0]

        content = path.read_text(encoding="utf-8")
        self._cache[key] = (content, mtime)
        return content

    # --- Public API ---

    def get_core_workflow(self) -> str:
        """Load the core workflow instructions (always in context)."""
        return self._read_with_cache(
            self._workflow_dir / "aws-aidlc-rules" / "core-workflow.md"
        )

    def get_detail(self, category: str, name: str) -> str:
        """Load a detail file by category and name.

        Args:
            category: 'common', 'inception', 'construction', or 'operations'
            name: filename without .md extension (e.g. 'audit-logging')
        """
        validate_category(category)
        validate_name(name, "detail name")
        path = (
            self._workflow_dir / "aws-aidlc-rule-details" / category / f"{name}.md"
        )
        ensure_within(path, self._workflow_dir)
        return self._read_with_cache(path)

    def get_template(self, name: str) -> str:
        """Load a template file by name."""
        path = self._workflow_dir / "templates" / f"{name}.md"
        return self._read_with_cache(path)

    def get_extension(self, name: str) -> str:
        """Load an extension file by name.

        Searches the standard extensions dir first, then extra dirs.
        Extensions live under aws-aidlc-rule-details/extensions/ and may
        be nested in subdirectories (e.g. 'security/baseline/security-baseline').

        Args:
            name: Extension name — either a flat stem ('my-ext') or a
                  slash-separated relative path ('security/baseline/security-baseline').
                  The .md suffix is added automatically.
        """
        validate_extension_path(name)
        std_ext_dir = (
            self._workflow_dir / "aws-aidlc-rule-details" / "extensions"
        )

        # Try standard extensions dir
        standard = std_ext_dir / f"{name}.md"
        ensure_within(standard, self._workflow_dir)
        if standard.is_file():
            return self._read_with_cache(standard)

        # Fall back to extra dirs in order
        for extra_dir in self._extra_extension_dirs:
            candidate = extra_dir / f"{name}.md"
            if candidate.is_file():
                return self._read_with_cache(candidate)

        raise FileNotFoundError(
            f"Extension '{name}' not found in any extension directory."
        )

    def list_extensions(self) -> list[dict[str, str]]:
        """List all available extensions with their metadata.

        Recursively scans extension directories for .md files, matching
        the upstream core-workflow.md expectation of nested extension dirs
        (e.g. extensions/security/baseline/security-baseline.md).

        Standard extensions dir is listed first; extra dirs are appended.
        Extensions with the same relative name are deduplicated (first wins).
        """
        seen: set[str] = set()
        extensions: list[dict[str, str]] = []

        std_ext_dir = self._workflow_dir / "aws-aidlc-rule-details" / "extensions"
        for ext_dir in [std_ext_dir, *self._extra_extension_dirs]:
            if not ext_dir.is_dir():
                continue
            for f in sorted(ext_dir.rglob("*.md")):
                # Build a relative name without the .md suffix
                rel = f.relative_to(ext_dir).with_suffix("")
                rel_name = str(rel)
                if rel_name in seen:
                    continue
                seen.add(rel_name)
                content = self._read_with_cache(f)
                desc = ""
                for line in content.splitlines():
                    if line.startswith("# "):
                        desc = line[2:].strip()
                        break
                extensions.append(
                    {"name": rel_name, "description": desc, "path": str(f)}
                )
        return extensions

    def list_details(self, category: str | None = None) -> list[dict[str, str]]:
        """List available detail files, optionally filtered by category."""
        details_dir = self._workflow_dir / "aws-aidlc-rule-details"
        results = []

        categories = (
            [category] if category
            else ["common", "inception", "construction", "operations"]
        )
        for cat in categories:
            cat_dir = details_dir / cat
            if not cat_dir.is_dir():
                continue
            for f in sorted(cat_dir.glob("*.md")):
                results.append({"category": cat, "name": f.stem, "path": str(f)})
        return results

    def get_stage_guidance(self, phase: str, stage: str) -> dict[str, str]:
        """Get all guidance needed for a specific stage.

        Returns dict with keys: 'stage_detail', and optionally 'extension' content.
        """
        result: dict[str, str] = {}

        # Map phase to detail category
        category_map = {
            "inception": "inception",
            "construction": "construction",
            "operations": "operations",
        }
        category = category_map.get(phase)
        if not category:
            raise ValueError(f"Unknown phase: {phase}")

        result["stage_detail"] = self.get_detail(category, stage)

        # Check for matching extensions under aws-aidlc-rule-details/extensions/
        # Extensions are cross-cutting constraints loaded recursively per core-workflow.md
        ext_dir = self._workflow_dir / "aws-aidlc-rule-details" / "extensions"
        if ext_dir.is_dir():
            for ext_file in sorted(ext_dir.rglob("*.md")):
                if ext_file.stem == stage:
                    rel = ext_file.relative_to(ext_dir).with_suffix("")
                    result[f"extension:{rel}"] = self._read_with_cache(ext_file)

        return result

    def get_common_startup_guidance(self) -> dict[str, str]:
        """Load the common files needed at workflow start."""
        startup_files = [
            "process-overview",
            "content-validation",
            "question-format-guide",
            "overconfidence-prevention",
        ]
        result = {}
        for name in startup_files:
            try:
                result[name] = self.get_detail("common", name)
            except FileNotFoundError:
                logger.warning(f"Common startup file not found: {name}.md")
        return result

    def preload_extensions(self) -> list[str]:
        """Eagerly read all extension files into cache.

        Called at server startup so the LLM has immediate awareness of
        all custom extensions and their behavior without a separate
        list+read round-trip.

        Returns the names of extensions that were loaded.
        """
        loaded = []
        for ext_dir in [
            self._workflow_dir / "aws-aidlc-rule-details" / "extensions",
            *self._extra_extension_dirs,
        ]:
            if not ext_dir.is_dir():
                continue
            for f in sorted(ext_dir.rglob("*.md")):
                try:
                    self._read_with_cache(f)
                    rel = f.relative_to(ext_dir).with_suffix("")
                    loaded.append(str(rel))
                    logger.debug(f"Preloaded extension: {rel}")
                except Exception as e:
                    logger.warning(f"Failed to preload extension {f}: {e}")
        if loaded:
            logger.info(f"Preloaded {len(loaded)} extension(s): {loaded}")
        else:
            logger.info("No extensions found to preload.")
        return loaded

    def invalidate_cache(self) -> int:
        """Clear the entire cache. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count
