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
    assert "could only read" not in source
    assert "had read-only file tools and no web access" in " ".join(
        re.sub(r'"\\s*"', "", source).split()
    )


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


def test_vendored_docs_keep_the_workflow_overlay():
    for rel in ("docs/SETUP.md", "docs/SETUP.zh-TW.md", "docs/CONTROL_AVAILABILITY.md", "CHANGELOG.md"):
        assert "SKILL.md" not in (ARS / rel).read_text(encoding="utf-8"), rel
