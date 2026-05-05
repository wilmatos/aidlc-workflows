"""Tests for the MCP server tools."""


from aidlc_mcp_server.server import PHASE_ORDER, PHASES, _next_stage


class TestNextStage:
    def test_next_stage_within_phase(self):
        result = _next_stage("inception", "workspace-detection")
        assert result["status"] == "next_stage"
        assert result["stage"] == "reverse-engineering"
        assert result["phase"] == "inception"

    def test_next_stage_cross_phase(self):
        result = _next_stage("inception", "units-generation")
        assert result["status"] == "next_phase"
        assert result["phase"] == "construction"
        assert result["stage"] == "functional-design"

    def test_workflow_complete(self):
        result = _next_stage("operations", "operations")
        assert result["status"] == "workflow_complete"
        assert result["stage"] is None

    def test_unknown_stage(self):
        result = _next_stage("inception", "nonexistent")
        assert result["status"] == "unknown_stage"

    def test_all_phases_connected(self):
        """Verify every phase's last stage leads to the next phase."""
        for i, phase in enumerate(PHASE_ORDER[:-1]):
            last_stage = PHASES[phase][-1]
            result = _next_stage(phase, last_stage)
            assert result["status"] == "next_phase"
            assert result["phase"] == PHASE_ORDER[i + 1]

    def test_all_stages_have_next(self):
        """Every non-last stage should have a next_stage."""
        for phase, stages in PHASES.items():
            for stage in stages[:-1]:
                result = _next_stage(phase, stage)
                assert result["status"] == "next_stage"
                assert result["stage"] is not None
