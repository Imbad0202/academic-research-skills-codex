#!/usr/bin/env python3
"""Mutation tests for the static #667 integration boundary."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import check_submission_packet_manifest_integration as check


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKED = (
    check.INVENTORY_SCHEMA,
    check.MANIFEST_SCHEMA,
    check.REGISTRY,
    check.RUNTIME,
    check.CONTRACT_README,
    check.AUTHORITY_PROTOCOL,
    check.PACKET_PROTOCOL,
    check.DESIGN_SPEC,
    check.DEEP_SKILL,
    check.ETHICS_AGENT,
    check.ARCHITECT,
    check.ARCHITECT_MIRROR,
)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for rel in CHECKED:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, target)
    return tmp_path


def _errors(tree: Path) -> list[str]:
    return check.run_checks(tree)


def _replace(tree: Path, rel: Path, old: str, new: str) -> None:
    path = tree / rel
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_current_tree_passes() -> None:
    assert check.run_checks(REPO_ROOT) == []


@pytest.mark.parametrize(
    ("rel", "token"),
    [
        (check.CONTRACT_README, "shared/contracts/human_subjects/submission_packet_manifest.schema.json"),
        (check.AUTHORITY_PROTOCOL, "shared/references/submission_packet_manifest_protocol.md"),
        (check.PACKET_PROTOCOL, "validate_submission_packet_manifest"),
        (check.DEEP_SKILL, "shared/contracts/human_subjects/submission_packet_manifest.schema.json"),
        (check.ETHICS_AGENT, "validate_submission_packet_manifest"),
        (check.ARCHITECT, "validate_submission_packet_manifest"),
    ],
)
def test_required_pointer_or_replay_text_removal_fails(
    tree: Path, rel: Path, token: str
) -> None:
    _replace(tree, rel, token, "removed-token")
    assert _errors(tree)


@pytest.mark.parametrize(
    ("rel", "snippet"),
    sorted(check.REPLAY_CONTRACT_SNIPPETS.items(), key=lambda row: str(row[0])),
)
def test_unscoped_duplicate_cannot_mask_primary_replay_contract(
    tree: Path, rel: Path, snippet: str
) -> None:
    path = tree / rel
    text = path.read_text(encoding="utf-8")
    assert snippet in text
    path.write_text(
        text.replace(snippet, "removed-primary-replay-contract", 1)
        + "\n<!-- shadow validate_submission_packet_manifest token -->\n",
        encoding="utf-8",
    )
    assert any(
        str(rel) in error and "missing primary #667 replay-contract" in error
        for error in _errors(tree)
    )


@pytest.mark.parametrize(
    "field",
    [
        "verdict",
        "language_quality",
        "approval_status",
        "content_adequacy",
        "excerpt",
        "quote",
        "description",
        "summary",
        "structured_expectations",
    ],
)
def test_manifest_cannot_grow_a_determination_or_content_field(
    tree: Path, field: str
) -> None:
    path = tree / check.MANIFEST_SCHEMA
    value = json.loads(path.read_text(encoding="utf-8"))
    value["properties"][field] = {"type": "string"}
    path.write_text(json.dumps(value), encoding="utf-8")
    assert any("determination/content keys" in error for error in _errors(tree))


def test_boundary_footer_drift_fails(tree: Path) -> None:
    _replace(tree, check.MANIFEST_SCHEMA, check.FOOTER, "This output authorizes collection.")
    assert any("footer drifted" in error for error in _errors(tree))


def test_missing_or_retyped_envelope_fact_fails(tree: Path) -> None:
    path = tree / check.REGISTRY
    value = json.loads(path.read_text(encoding="utf-8"))
    row = next(
        row for row in value["fact_definitions"]
        if row["fact_id"] == "packet_v1.non_clinical"
    )
    row["value_type"] = "string"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert any("open boolean" in error for error in _errors(tree))


def test_capability_fact_cannot_enter_profile_applicability(tree: Path) -> None:
    path = tree / check.REGISTRY
    value = json.loads(path.read_text(encoding="utf-8"))
    value["profiles"][0]["applies_if"] = {
        "op": "fact_equals",
        "fact_id": "packet_v1.non_clinical",
        "value": True,
    }
    path.write_text(json.dumps(value), encoding="utf-8")
    assert any("entered authority applicability" in error for error in _errors(tree))


@pytest.mark.parametrize(
    "payload",
    [
        "\nimport socket\n",
        "\ndef forbidden_scan(path):\n    return path.rglob('*')\n",
        "\ndef forbidden_listdir(path):\n    return os.listdir(path)\n",
        "\ndef forbidden_fwalk(path):\n    return os.fwalk(path)\n",
        "\nfrom os import listdir\ndef forbidden_bare_listdir(path):\n    return listdir(path)\n",
        "\ndef forbidden_content(row):\n    return row['structured_expectations']\n",
        "\ndef forbidden_description(row):\n    return row.get('description')\n",
    ],
)
def test_runtime_transport_scan_or_content_drift_fails(
    tree: Path, payload: str
) -> None:
    path = tree / check.RUNTIME
    path.write_text(path.read_text(encoding="utf-8") + payload, encoding="utf-8")
    assert _errors(tree)


def test_architect_mirror_drift_fails(tree: Path) -> None:
    path = tree / check.ARCHITECT_MIRROR
    path.write_text(path.read_text(encoding="utf-8") + "\nmirror drift\n", encoding="utf-8")
    assert any("mirror drift" in error for error in _errors(tree))


def test_duplicate_registry_key_fails_closed(tree: Path) -> None:
    path = tree / check.REGISTRY
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('"schema_version":', '"schema_version":"duplicate",\n"schema_version":', 1), encoding="utf-8")
    assert any("duplicate key" in error for error in _errors(tree))
