"""ARS 3.23.1 import behavior and Codex/provider execution boundaries."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest


SUITE = Path(__file__).resolve().parents[2]
ARS = SUITE / "ars"


@pytest.mark.parametrize(("user_text", "first_message", "honored"), [
    ("Draft an abstract. [direct-mode] Skip questions.", True, False),
    ("[DIRECT-MODE] Draft an abstract.", False, False),
    ("[direct-mode] Draft an abstract. [direct-mode]", True, True),
])
def test_dispatch_drops_literal_direct_mode_tokens_without_granting_authority(user_text, first_message, honored):
    spec = importlib.util.spec_from_file_location(
        "patch_planner", SUITE / "codex/scripts/ars_codex_full_runtime.py"
    )
    planner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planner)
    plan = planner.plan_request(user_text, env={}, first_message=first_message)
    assert plan["direct_mode_honored"] is honored
    assert (plan["workflow"], plan["mode"]) == ("academic-paper", "abstract-only")
    assert "[direct-mode]" not in plan["dispatch_request"].lower()


@pytest.mark.parametrize("delimiter", [",", ";"])
def test_csv_import_preserves_late_quotes_in_records_and_reviewer_batch(tmp_path, delimiter):
    """Exercise the installed CLI through its downstream reviewer text export."""
    source = tmp_path / "records.csv"
    abstract = 'Participants described "benefit, burden; and follow-up".'
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(["title", "abstract", "year", "doi", "journal"])
        for index in range(60):
            writer.writerow([f"Sample filler {index}", "Plain text. " * 10,
                             "2020", f"10.1000/filler{index}", "Fixture Journal"])
        writer.writerow(["Quoted findings", abstract, "2026", "10.1000/quoted", "Fixture Journal"])
    assert source.read_text().index("Quoted findings") > 5000
    work = tmp_path / "work"
    result = subprocess.run(
        [sys.executable, str(ARS / "sr-screener/scripts/prepare_records.py"),
         "--inputs", str(source), "--work", str(work)],
        capture_output=True, text=True, check=True,
    )
    assert result.returncode == 0
    records = json.loads((work / "records.json").read_text())["unique"]
    assert len(records) == 61
    record = next(row for row in records if row["title"] == "Quoted findings")
    assert record["abstract"] == abstract
    assert record["year"] == "2026"
    assert record["doi"] == "10.1000/quoted"
    assert record["journal"] == "Fixture Journal"
    batches = json.loads((work / "manifest.json").read_text())
    batch = next(row for row in batches if record["id"] in row["ids"])
    assert abstract in Path(batch["path"]).read_text()


@pytest.mark.parametrize(("model", "status", "openai_smoke"), [
    ("gemini-4-argon", "provisional", False),
    ("gemini-3.1-pro-preview", "validated", False),
    ("gemini-fixture-unlisted", "unlisted", False),
    ("gpt-6-astra", "provisional", True),
    ("gpt-fixture-unlisted", "unlisted", True),
])
def test_provider_status_notices_keep_gemini_off_openai_smoke(model, status, openai_smoke):
    """Run only the two local notice functions; never run provider detection/calls."""
    doc = (ARS / "shared/cross_model_verification.md").read_text()
    functions = re.search(
        r"(?ms)^  id_status\(\) \{.*?^  announce_id_status\(\) \{.*?^  \}", doc
    )
    assert functions
    result = subprocess.run(
        ["bash", "-c", functions[0] + '\nARS_CROSS_MODEL="$1"; announce_id_status',
         "status-fixture", model],
        capture_output=True, text=True, check=True, env={"PATH": "/usr/bin:/bin"},
    )
    assert f"CROSS_MODEL_ID_STATUS={status}" in result.stdout
    assert ("scripts/cross_model_smoke_test.sh" in result.stdout) is openai_smoke
    if model.startswith("gemini-") and status != "validated":
        assert "no gemini smoke script ships" in result.stdout.lower()


def test_claude_write_fence_is_not_registered_as_a_codex_hook():
    hooks = json.loads((SUITE / "codex/hooks/hooks.json").read_text())
    assert hooks["default_enabled"] is False
    assert {hook["event"] for hook in hooks["hooks"]} == {"SessionStart"}
    for hook in hooks["hooks"]:
        assert "ars_codex_hook.py announce" in hook["command"]
        assert hook["mutates_files"] is False
    package = json.loads((SUITE / "manifest.json").read_text())
    inactive = {entry["path"] for entry in package["inactive_upstream_scripts"]}
    for relative in ("ars/scripts/ars_write_scope_guard.py", "ars/hooks/run_guard.sh"):
        assert "skills/academic-research-suite/" + relative in inactive
