# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Tests for input validation and path safety."""


import pytest

from aidlc_mcp_server.validation import (
    MAX_DELIVERABLE_SIZE,
    ensure_within,
    validate_category,
    validate_content_size,
    validate_extension_path,
    validate_name,
    validate_workspace,
)


class TestValidateName:
    def test_valid_names(self):
        assert validate_name("my-project", "test") == "my-project"
        assert validate_name("project_1", "test") == "project_1"
        assert validate_name("A", "test") == "A"
        assert validate_name("workspace-detection", "test") == "workspace-detection"

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError):
            validate_name("../../etc", "test")

    def test_rejects_slashes(self):
        with pytest.raises(ValueError):
            validate_name("path/traversal", "test")

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_name("", "test")

    def test_rejects_dots_only(self):
        with pytest.raises(ValueError):
            validate_name("..", "test")

    def test_rejects_leading_hyphen(self):
        with pytest.raises(ValueError):
            validate_name("-bad-name", "test")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError):
            validate_name("has spaces", "test")


class TestValidateCategory:
    def test_valid_categories(self):
        for cat in ["common", "inception", "construction", "operations"]:
            assert validate_category(cat) == cat

    def test_rejects_invalid(self):
        with pytest.raises(ValueError):
            validate_category("../../etc")

    def test_rejects_unknown(self):
        with pytest.raises(ValueError):
            validate_category("unknown")


class TestValidateWorkspace:
    def test_valid_workspace(self, tmp_path):
        ws = validate_workspace(str(tmp_path))
        assert ws == tmp_path.resolve()

    def test_rejects_nonexistent(self):
        with pytest.raises(ValueError, match="does not exist"):
            validate_workspace("/nonexistent/path/12345")

    def test_rejects_file(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hello")
        with pytest.raises(ValueError, match="does not exist"):
            validate_workspace(str(f))


class TestEnsureWithin:
    def test_valid_path(self, tmp_path):
        child = tmp_path / "sub" / "file.txt"
        result = ensure_within(child, tmp_path)
        assert str(result).startswith(str(tmp_path.resolve()))

    def test_rejects_escape(self, tmp_path):
        escaped = tmp_path / ".." / ".." / "etc"
        with pytest.raises(ValueError, match="escapes"):
            ensure_within(escaped, tmp_path)


class TestValidateContentSize:
    def test_valid_content(self):
        assert validate_content_size("hello") == "hello"

    def test_rejects_oversized(self):
        big = "x" * (MAX_DELIVERABLE_SIZE + 1)
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_content_size(big)


class TestProjectPathTraversal:
    """Verify that Project rejects path traversal attempts."""

    def test_rejects_traversal_in_name(self, tmp_path):
        from aidlc_mcp_server.project import Project
        with pytest.raises(ValueError):
            Project(tmp_path, "../../etc")

    def test_rejects_slash_in_name(self, tmp_path):
        from aidlc_mcp_server.project import Project
        with pytest.raises(ValueError):
            Project(tmp_path, "path/traversal")


class TestValidateExtensionPath:
    def test_flat_name(self):
        assert validate_extension_path("my-extension") == "my-extension"

    def test_nested_path(self):
        result = validate_extension_path(
            "security/baseline/security-baseline"
        )
        assert result == "security/baseline/security-baseline"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_extension_path("")

    def test_rejects_traversal(self):
        with pytest.raises(ValueError):
            validate_extension_path("../etc/passwd")

    def test_rejects_double_dot_segment(self):
        with pytest.raises(ValueError):
            validate_extension_path("security/../../../etc")

    def test_rejects_empty_segment(self):
        with pytest.raises(ValueError):
            validate_extension_path("security//baseline")

    def test_rejects_leading_hyphen_segment(self):
        with pytest.raises(ValueError):
            validate_extension_path("security/-bad")

    def test_rejects_spaces_in_segment(self):
        with pytest.raises(ValueError):
            validate_extension_path("security/has spaces")
