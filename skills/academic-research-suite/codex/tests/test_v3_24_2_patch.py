"""ARS 3.24.2 experiment locks, methods text, and Codex overlays."""

from __future__ import annotations

import json
import re
from pathlib import Path


SUITE = Path(__file__).resolve().parents[2]
ARS = SUITE / "ars"


def _section() -> str:
    router = (SUITE / "SKILL.md").read_text(encoding="utf-8")
    section = router.split("### ARS v3.24.2 Experiment Locks and Methods Text", 1)[1]
    return section.split("\n### ", 1)[0]


def test_router_states_the_compatibility_breaks():
    section = " ".join(_section().split())
    for required in (
        "`repro_lock: null` with a `repro_lock_reason`",
        "Earlier ARS-Codex releases reject this form",
        "does not prove the lock does not apply",
        "`cross_model.secondary_model_id` may still be null",
        "Some passports that passed before now fail",
        "correct it by hand",
    ):
        assert required in section, required


def test_methods_text_states_what_the_tool_list_enforces():
    source = (ARS / "sr-screener/scripts/build_outputs.py").read_text(encoding="utf-8")
    joined = " ".join(re.sub(r'"\s*"', "", source).split())
    assert "could only read" not in joined
    assert (
        "The reviewer agents had read-only file tools and no web access; "
        "each was instructed to read only the file it was given."
    ) in joined


def test_gates_register_the_hermetic_lock_tests():
    runtime = json.loads((SUITE / "codex/full-runtime-manifest.json").read_text(encoding="utf-8"))
    gates = {gate["id"]: gate for gate in runtime["quality_gates"]}
    for gate_id, script in (
        ("v3242_repro_lock_gate", "test_check_repro_lock.py"),
        ("v3242_repro_lock_validation_drift", "test_repro_lock_validation_drift.py"),
        ("v3242_experiment_provenance", "test_experiment_provenance.py"),
    ):
        assert gates[gate_id]["runner"] == f"upstream:ars/scripts/{script}"
        assert gates[gate_id]["execution"] == "hermetic"
        assert (ARS / "scripts" / script).is_file()


def test_claude_channel_docs_keep_the_upstream_entry_name():
    setup = (ARS / "docs/SETUP.md").read_text(encoding="utf-8")
    setup_zh = (ARS / "docs/SETUP.zh-TW.md").read_text(encoding="utf-8")
    control = (ARS / "docs/CONTROL_AVAILABILITY.md").read_text(encoding="utf-8")
    for text in (setup, setup_zh):
        assert "ars-deep-research/SKILL.md" in text
        assert "ars-deep-research/WORKFLOW.md" not in text
    assert "a zip with `SKILL.md` at the top" in " ".join(control.split())
    for text in (setup, setup_zh, control):
        assert "WORKFLOW.md" not in text


def test_new_changelog_text_keeps_the_workflow_overlay():
    assert "SKILL.md" not in (ARS / "CHANGELOG.md").read_text(encoding="utf-8")
