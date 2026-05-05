"""Tests for project state management."""

import pytest

from aidlc_mcp_server.project import Project


@pytest.fixture
def workspace(tmp_path):
    return tmp_path


@pytest.fixture
def project(workspace):
    return Project(workspace, "test-project")


class TestProject:
    def test_create_project(self, project):
        state = project.create("Build a web app", "suggest")
        assert state["name"] == "test-project"
        assert state["operational_mode"] == "suggest"
        assert state["current_phase"] == "inception"
        assert state["current_stage"] == "workspace-detection"
        assert project.exists()

    def test_create_duplicate_fails(self, project):
        project.create("Build a web app", "suggest")
        with pytest.raises(FileExistsError):
            project.create("Build another app", "suggest")

    def test_load_state(self, project):
        project.create("Build a web app", "suggest")
        state = project.load_state()
        assert state["name"] == "test-project"

    def test_load_nonexistent_fails(self, project):
        with pytest.raises(FileNotFoundError):
            project.load_state()

    def test_update_stage(self, project):
        project.create("Build a web app", "suggest")
        state = project.update_stage("inception", "requirements-analysis", "in_progress")
        assert state["current_stage"] == "requirements-analysis"
        assert state["phase_state"] == "in_progress"

    def test_complete_stage(self, project):
        project.create("Build a web app", "suggest")
        state = project.complete_stage("workspace-detection")
        assert "workspace-detection" in state["completed_stages"]
        assert state["phase_state"] == "completed"

    def test_skip_stage(self, project):
        project.create("Build a web app", "suggest")
        state = project.skip_stage("reverse-engineering", "Greenfield project")
        assert "reverse-engineering" in state["skipped_stages"]

    def test_save_deliverable(self, project):
        project.create("Build a web app", "suggest")
        path = project.save_deliverable("inception", "requirements-analysis", "# Requirements\n\nContent here")
        assert path.is_file()
        assert "Requirements" in path.read_text()
