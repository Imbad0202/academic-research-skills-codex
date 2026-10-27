"""ARS 3.24.0 review-letter attachments and Codex execution boundaries."""

from __future__ import annotations

import json
import re
from pathlib import Path


SUITE = Path(__file__).resolve().parents[2]
ARS = SUITE / "ars"


def _router() -> str:
    return (SUITE / "SKILL.md").read_text(encoding="utf-8")


def test_suggested_reference_lookup_needs_an_explicit_request():
    router = _router()
    row = next(
        line for line in router.splitlines()
        if line.startswith("| Suggested-reference check (v3.24.0, #1001) |")
    )
    assert "Do not run `verify_panel_recommendations.py` automatically" in row
    assert "did not run" in row
    assert "An explicit request" in row


def test_reviewer_claim_check_requires_an_isolated_worker():
    section = _router().split("### ARS v3.24.0 Review-Letter Attachments", 1)[1]
    section = section.split("\n### ", 1)[0]
    assert "`ARS_PANEL_CLAIM_CHECK=0`" in section
    assert "no tools, browsing, file access, or inherited conversation" in section
    assert "never judge the findings inline" in section
    assert "acronym\n  check, which stays the letter's last section" in section


def _letter_template_headings(template: str) -> list[str]:
    """H2 headings inside the fenced letter template that holds the attachments."""
    blocks = re.findall(r"^```[^\n]*\n(.*?)^```", template, re.M | re.S)
    letter = next(block for block in blocks if "## Attachment: Acronym Check" in block)
    return re.findall(r"^## (.+)$", letter, re.M)


def test_letter_template_keeps_attachment_order_and_codex_entry_paths():
    template = (ARS / "academic-paper-reviewer/templates/editorial_decision_template.md").read_text(
        encoding="utf-8"
    )
    assert _letter_template_headings(template)[-3:] == [
        "Attachment: Suggested-Reference Check (advisory, #1001)",
        "Attachment: Reviewer Claim Check (advisory, #1002)",
        "Attachment: Acronym Check (advisory, #849)",
    ]
    assert "`SKILL.md`" not in template


def test_letter_template_check_rejects_a_section_after_the_acronym_check():
    template = (ARS / "academic-paper-reviewer/templates/editorial_decision_template.md").read_text(
        encoding="utf-8"
    )
    anchor = "## Attachment: Acronym Check (advisory, #849)"
    broken = template.replace(anchor, anchor + "\n\n## Trailing Section\n", 1)
    assert _letter_template_headings(broken)[-1] == "Trailing Section"


def test_new_degradation_anchors_use_the_codex_workflow_entry():
    registry = (ARS / "shared/contracts/degradation_registry.json").read_text(encoding="utf-8")
    assert "academic-paper-reviewer/SKILL.md" not in registry
    for path in re.findall(r'"file": "([^"]+)"', registry):
        assert (ARS / path).is_file(), path


def test_held_out_dispatcher_is_inactive_and_hermetic_tests_are_gates():
    package = json.loads((SUITE / "manifest.json").read_text(encoding="utf-8"))
    inactive = {entry["path"] for entry in package["inactive_upstream_scripts"]}
    dispatcher = "skills/academic-research-suite/ars/scripts/dispatch_panel_claim_audit.py"
    assert dispatcher in inactive

    runtime = json.loads((SUITE / "codex/full-runtime-manifest.json").read_text(encoding="utf-8"))
    gates = {gate["id"]: gate for gate in runtime["quality_gates"]}
    for gate_id, script in (
        ("v3240_panel_suggested_references", "test_verify_panel_recommendations.py"),
        ("v3240_panel_claim_check", "test_audit_panel_claims.py"),
        ("v3240_extract_panel_claims", "test_extract_panel_claims.py"),
    ):
        assert gates[gate_id]["runner"] == f"upstream:ars/scripts/{script}"
        assert gates[gate_id]["execution"] == "hermetic"
    assert not any("dispatch_panel_claim_audit" in gate["runner"] for gate in gates.values())
    rule = runtime["agent_team_rules"]["review_letter_attachments"]
    for required in (
        "after any consented cross-model decision check",
        "suggested-reference check, then the reviewer claim check, before the final acronym check",
        "only on an explicit user request",
        "ARS_PANEL_CLAIM_CHECK=0",
        "fresh, tool-less native worker",
        "never judged inline",
        "Neither attachment feeds the decision",
    ):
        assert required in rule, required
