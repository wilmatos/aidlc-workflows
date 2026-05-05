"""Tests for the workflow loader."""

from pathlib import Path

import pytest

from aidlc_mcp_server.workflow_loader import WorkflowLoader


@pytest.fixture
def loader():
    """Create a loader pointing at the real aidlc-rules directory."""
    root = Path(__file__).parent.parent
    # New flat layout (after sync script)
    flat = root / "aidlc-rules"
    if (flat / "aws-aidlc-rules").is_dir():
        return WorkflowLoader(flat)
    # Legacy subtree layout
    nested = root / "aidlc-rules" / "aidlc-rules"
    if nested.is_dir():
        return WorkflowLoader(nested)
    pytest.skip("aidlc-rules directory not found")


class TestWorkflowLoader:
    def test_get_core_workflow(self, loader):
        content = loader.get_core_workflow()
        assert len(content) > 0

    def test_get_detail_common(self, loader):
        content = loader.get_detail("common", "content-validation")
        assert len(content) > 0

    def test_get_detail_inception(self, loader):
        content = loader.get_detail("inception", "workspace-detection")
        assert len(content) > 0

    def test_get_detail_not_found(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.get_detail("common", "nonexistent-file")

    def test_list_details_all(self, loader):
        details = loader.list_details()
        assert len(details) > 10
        categories = {d["category"] for d in details}
        assert "common" in categories
        assert "inception" in categories
        assert "construction" in categories

    def test_list_details_filtered(self, loader):
        details = loader.list_details("inception")
        assert all(d["category"] == "inception" for d in details)
        names = {d["name"] for d in details}
        assert "workspace-detection" in names
        assert "requirements-analysis" in names

    def test_get_stage_guidance(self, loader):
        guidance = loader.get_stage_guidance("inception", "workspace-detection")
        assert "stage_detail" in guidance
        assert len(guidance["stage_detail"]) > 0

    def test_get_common_startup_guidance(self, loader):
        common = loader.get_common_startup_guidance()
        assert "question-format-guide" in common
        assert "content-validation" in common
        assert len(common) >= 1

    def test_cache_invalidation(self, loader):
        # Load a file to populate cache
        loader.get_core_workflow()
        count = loader.invalidate_cache()
        assert count >= 1
        # Reload should work fine
        content = loader.get_core_workflow()
        assert len(content) > 0

    def test_cache_returns_same_content(self, loader):
        content1 = loader.get_core_workflow()
        content2 = loader.get_core_workflow()
        assert content1 == content2

    def test_list_extensions(self, loader):
        # Should not fail even if no extensions exist yet
        extensions = loader.list_extensions()
        assert isinstance(extensions, list)

    def test_list_extensions_finds_nested(self, loader):
        """Extensions in subdirectories are discovered recursively."""
        extensions = loader.list_extensions()
        names = {e["name"] for e in extensions}
        assert "security/baseline/security-baseline" in names

    def test_list_extensions_metadata(self, loader):
        """Each extension entry has name, description, and path."""
        extensions = loader.list_extensions()
        assert len(extensions) >= 1
        ext = extensions[0]
        assert "name" in ext
        assert "description" in ext
        assert "path" in ext
        assert len(ext["description"]) > 0

    def test_get_extension_nested(self, loader):
        """Can load an extension by its nested relative path."""
        content = loader.get_extension(
            "security/baseline/security-baseline"
        )
        assert "Baseline Security Rules" in content

    def test_get_extension_not_found(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.get_extension("nonexistent-extension")

    def test_get_extension_traversal_rejected(self, loader):
        """Directory traversal in extension names is rejected."""
        with pytest.raises(ValueError):
            loader.get_extension("../../etc/passwd")

    def test_preload_extensions_finds_nested(self, loader):
        """Preload discovers nested extension files."""
        loaded = loader.preload_extensions()
        assert "security/baseline/security-baseline" in loaded
