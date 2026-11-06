"""ARS 3.24.1 reviewer card confirmation and Codex overlays."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SUITE = Path(__file__).resolve().parents[2]
ARS = SUITE / "ars"


def _section() -> str:
    router = (SUITE / "SKILL.md").read_text(encoding="utf-8")
    section = router.split("### ARS v3.24.1 Reviewer Card Confirmation", 1)[1]
    return section.split("\n### ", 1)[0]


def test_router_stops_after_phase_zero_for_native_workers_and_inline_roles():
    section = _section()
    for required in (
        "end the turn",
        "A native worker\n  that runs Phase 0 returns the cards and starts no seat",
        "Inline role execution\n  stops at the same point",
        "`[direct-mode]`",
        "is unmeasured",
    ):
        assert required in section, required


def test_card_confirmation_lint_passes_on_the_codex_workflow():
    result = subprocess.run(
        [sys.executable, str(ARS / "scripts/check_reviewer_card_confirmation.py")],
        capture_output=True,
        text=True,
        cwd=ARS,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_codex_entry_files_use_workflow_not_skill_md():
    lint = (ARS / "scripts/check_reviewer_card_confirmation.py").read_text(encoding="utf-8")
    assert 'SKILL = "academic-paper-reviewer/WORKFLOW.md"' in lint
    for rel in (
        "academic-pipeline/agents/pipeline_orchestrator_agent.md",
        "README.pt-BR.md",
    ):
        assert "SKILL.md" not in (ARS / rel).read_text(encoding="utf-8"), rel


def test_gate_rule_and_team_templates_record_the_stop():
    runtime = json.loads((SUITE / "codex/full-runtime-manifest.json").read_text(encoding="utf-8"))
    gates = {gate["id"]: gate for gate in runtime["quality_gates"]}
    gate = gates["v3241_reviewer_card_confirmation"]
    assert gate["runner"] == "upstream:ars/scripts/test_check_reviewer_card_confirmation.py"
    assert gate["execution"] == "hermetic"
    rule = runtime["agent_team_rules"]["reviewer_card_confirmation"]
    assert "returns the cards and starts no seat" in rule
    assert "[direct-mode]" in rule
    panel = (SUITE / "codex/agents/paper-reviewer-panel.md").read_text(encoding="utf-8")
    assert "## Card Confirmation Contract" in panel
    orchestrator = (SUITE / "codex/agents/academic-pipeline-orchestrator.md").read_text(encoding="utf-8")
    assert "after the reviewer's Phase 0" in orchestrator


def test_agent_prompt_files_keep_their_underscore_names_for_file_path_loading():
    for rel in (
        "agents/synthesis_agent.md",
        "agents/research_architect_agent.md",
        "agents/report_compiler_agent.md",
        "agents/screening_reviewer_agent.md",
        "sr-screener/agents/screening_reviewer_agent.md",
    ):
        assert (ARS / rel).is_file(), rel


def test_reviewer_output_labels_do_not_claim_independence():
    panel = (SUITE / "codex/agents/paper-reviewer-panel.md").read_text(encoding="utf-8")
    fixture = (SUITE / "codex/tests/fixtures/reviewer_full_seat_sections.md").read_text(encoding="utf-8")
    assert "Independent Reviewer" not in panel
    assert "Independent Reviewer" not in fixture
    assert "## Independence Contract" not in panel
    assert "`Reviewer Seat: Journal-Fit`" in panel
    assert "do not describe them as independent reviews" in panel.replace("\n", " ")
