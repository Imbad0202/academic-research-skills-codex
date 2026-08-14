#!/usr/bin/env python3
"""Hermetic replay, aggregation, renderer, and security tests for #681."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import shutil
import socket
import subprocess
import sys
import urllib.parse
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

import build_content_coverage_advisory as coverage_runtime
from build_content_coverage_advisory import (
    ContentCoverageAdvisoryError,
    finalize_advisory,
    main,
    render_advisory,
    validate_advisory,
)
from build_submission_packet_manifest import build_submission_packet_manifest
from resolve_human_subjects_authority import digest, resolve
from test_build_submission_packet_manifest import (
    PACKET_ROOT as SYNTHETIC_PACKET_ROOT,
    _repin_overlay,
    _synthetic_overlay_authority,
    _waiver_inventory,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "scripts" / "fixtures" / "content_coverage_advisory"
PACKET_ROOT = FIXTURES / "packet"
BASE_INVENTORY = FIXTURES / "base_inventory.json"
BASE_DRAFT = FIXTURES / "base_draft.json"
SESSION_SOURCES = FIXTURES / "session_sources.json"
AUTHORITY_FIXTURES = REPO_ROOT / "scripts" / "fixtures" / "human_subjects_authority"
REGISTRY_PATH = REPO_ROOT / "shared" / "human_subjects_authority_registry.json"
ROW_SCHEMA_PATH = (
    REPO_ROOT / "shared" / "contracts" / "evidence" / "evidence_row_v1_1.schema.json"
)
ADVISORY_SCHEMA_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "human_subjects"
    / "content_coverage_advisory.schema.json"
)
RUNTIME_PATH = REPO_ROOT / "scripts" / "build_content_coverage_advisory.py"

REQUIREMENT_ID = "us.45cfr46.116.informed-consent"
REQUIREMENT_POINTER = "/profiles/0/requirements/1"
EXPECTATION_POINTERS = [
    f"{REQUIREMENT_POINTER}/structured_expectations/{index}" for index in range(3)
]
SOURCE_TEXT = (
    "Participation is voluntary. Prospective information is provided before consent.\n"
)
CAPTURED_AT = "2026-08-09T12:00:00Z"
ENVELOPE_EXPECTED = {
    "packet_v1.non_clinical": True,
    "packet_v1.single_institution": True,
    "packet_v1.competent_adults_only": True,
    "packet_v1.biospecimens_involved": False,
    "packet_v1.regulated_clinical_trial": False,
    "packet_v1.cross_border_material_transfer": False,
    "packet_v1.multisite_reliance": False,
}
REASON_CODES = {
    "ALL_EXPECTATIONS_APPEAR_COVERED",
    "EXPECTATION_NOT_LOCATED",
    "CONFLICTING_COVERAGE_OBSERVATIONS",
    "COVERAGE_CHECK_NOT_PERFORMED",
    "SESSION_CONTENT_NOT_PROVIDED",
    "SOURCE_ACCESS_FAILED",
    "SOURCE_RETRIEVAL_FAILED",
    "DETERMINISTIC_PACKET_GAP",
    "DETERMINISTIC_PACKET_CONFLICT",
    "WAIVER_OR_EXCEPTION_BOUNDARY",
    "EXTERNAL_DEPENDENCY",
    "APPLICABILITY_UNRESOLVED",
    "NO_PROFILED_STRUCTURED_EXPECTATIONS",
    "INSTITUTIONAL_ACCEPTANCE_REQUIRED",
}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _inventory() -> dict[str, Any]:
    return _json(BASE_INVENTORY)


def _draft() -> dict[str, Any]:
    return _json(BASE_DRAFT)


def _sources() -> dict[str, str]:
    return _json(SESSION_SOURCES)  # type: ignore[return-value]


def _registry() -> dict[str, Any]:
    return _json(REGISTRY_PATH)


def _context() -> dict[str, Any]:
    context = _json(AUTHORITY_FIXTURES / "us-gdpr-two-axis.json")
    known = {row["fact_id"] for row in context["declared_facts"]}
    for fact_id, value in ENVELOPE_EXPECTED.items():
        if fact_id not in known:
            context["declared_facts"].append(
                {
                    "fact_id": fact_id,
                    "value_type": "boolean",
                    "state": "declared",
                    "value": value,
                    "provenance": "author_declared",
                }
            )
    return context


def _repin_profile(context: dict[str, Any], profile: dict[str, Any]) -> None:
    unsigned = copy.deepcopy(profile)
    unsigned.pop("profile_digest", None)
    profile["profile_digest"] = digest(unsigned)
    selected = next(
        row
        for row in context["selected_profiles"]
        if row["profile_id"] == profile["profile_id"]
    )
    selected["profile_digest"] = profile["profile_digest"]
    display = next(
        row
        for axis in context["display_precedence"]
        for row in axis["ordered_authorities"]
        if row["authority_kind"] == "profile"
        and row["authority_id"] == profile["profile_id"]
    )
    display["authority_digest"] = profile["profile_digest"]


def _us_profile(registry: dict[str, Any]) -> dict[str, Any]:
    return next(
        row
        for row in registry["profiles"]
        if row["profile_id"] == "us.hhs.45-cfr-46.subpart-a"
    )


def _us_requirement(registry: dict[str, Any]) -> dict[str, Any]:
    return next(
        row
        for row in _us_profile(registry)["requirements"]
        if row["requirement_id"] == REQUIREMENT_ID
    )


def _case(
    *,
    inventory: dict[str, Any] | None = None,
    packet_root: Path = PACKET_ROOT,
    context: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    draft: dict[str, Any] | None = None,
    sources: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    inventory = _inventory() if inventory is None else inventory
    context = _context() if context is None else context
    registry = _registry() if registry is None else registry
    resolved = resolve(context, registry)
    manifest = build_submission_packet_manifest(
        inventory,
        packet_root,
        context=context,
        registry=registry,
        resolved=resolved,
    )
    return {
        "inventory": inventory,
        "packet_root": packet_root,
        "context": context,
        "registry": registry,
        "resolved": resolved,
        "manifest": manifest,
        "draft": _draft() if draft is None else draft,
        "sources": _sources() if sources is None else dict(sources),
    }


def _finalize(case: dict[str, Any]) -> dict[str, Any]:
    return finalize_advisory(
        case["draft"],
        case["inventory"],
        case["packet_root"],
        case["context"],
        case["registry"],
        case["resolved"],
        case["manifest"],
        case["sources"],
    )


def _validate(advisory: dict[str, Any], case: dict[str, Any]) -> None:
    validate_advisory(
        advisory,
        case["draft"],
        case["inventory"],
        case["packet_root"],
        case["context"],
        case["registry"],
        case["resolved"],
        case["manifest"],
        case["sources"],
    )


def _render(
    advisory: dict[str, Any],
    case: dict[str, Any],
    *,
    page: int = 1,
    page_size: int = 25,
) -> str:
    return render_advisory(
        advisory,
        case["draft"],
        case["inventory"],
        case["packet_root"],
        case["context"],
        case["registry"],
        case["resolved"],
        case["manifest"],
        case["sources"],
        page=page,
        page_size=page_size,
    )


def _result(advisory: dict[str, Any], requirement_id: str = REQUIREMENT_ID) -> dict[str, Any]:
    matches = [
        row
        for row in advisory["requirement_results"]
        if row["requirement_ref"]["requirement_id"] == requirement_id
    ]
    assert len(matches) == 1, (requirement_id, matches)
    return matches[0]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _repin_report(advisory: dict[str, Any]) -> None:
    advisory.pop("report_digest", None)
    advisory["report_digest"] = digest(advisory)


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _not_located(judgment: dict[str, Any]) -> None:
    judgment.update(
        {
            "coverage_check_state": "performed",
            "advisory_coverage_status": "NOT_LOCATED",
            "quoted_anchor_encoded": "",
            "captured_at": None,
            "failure_state": None,
        }
    )


def _not_checked(judgment: dict[str, Any], failure_state: str) -> None:
    judgment.update(
        {
            "coverage_check_state": "not_checked",
            "advisory_coverage_status": None,
            "quoted_anchor_encoded": "",
            "captured_at": None,
            "failure_state": failure_state,
        }
    )


def _schema_validator() -> Draft202012Validator:
    row_schema = _json(ROW_SCHEMA_PATH)
    advisory_schema = _json(ADVISORY_SCHEMA_PATH)
    resources = Registry().with_resource(
        row_schema["$id"], Resource.from_contents(row_schema)
    )
    return Draft202012Validator(
        advisory_schema,
        registry=resources,
        format_checker=FormatChecker(),
    )


def _draft_errors(draft: dict[str, Any]) -> list[Any]:
    validator = _schema_validator()
    subschema = validator.schema["$defs"]["advisory_draft"]
    return list(validator.evolve(schema=subschema).iter_errors(draft))


def _packet_copy(tmp_path: Path) -> Path:
    target = tmp_path / "packet"
    shutil.copytree(PACKET_ROOT, target)
    return target


def _set_packet_text(
    packet_root: Path,
    inventory: dict[str, Any],
    text: str,
    *,
    artifact_id: str = "fixture.us-consent",
) -> None:
    artifact = next(
        row for row in inventory["artifacts"] if row["artifact_id"] == artifact_id
    )
    path = packet_root / artifact["relative_path"]
    path.write_text(text, encoding="utf-8")
    payload = text.encode("utf-8")
    artifact["declared_sha256"] = hashlib.sha256(payload).hexdigest()
    artifact["declared_size_bytes"] = len(payload)


def _synthetic_live_draft_and_sources() -> tuple[dict[str, Any], dict[str, str]]:
    source = (SYNTHETIC_PACKET_ROOT / "consent-materials.txt").read_text(
        encoding="utf-8"
    )
    draft = _draft()
    for judgment in list(draft["judgments"]):
        judgment["quoted_anchor_encoded"] = _quote(source.strip())
    return draft, {"fixture.us-consent": source}


def _expectation_count_case(count: int) -> dict[str, Any]:
    context = _context()
    registry = _registry()
    profile = _us_profile(registry)
    requirement = _us_requirement(registry)
    template = copy.deepcopy(requirement["structured_expectations"][0])
    requirement["structured_expectations"] = []
    judgments: list[dict[str, Any]] = []
    for index in range(count):
        expectation = copy.deepcopy(template)
        expectation["field_id"] = f"synthetic.coverage-field-{index:04d}"
        requirement["structured_expectations"].append(expectation)
        judgments.append(
            {
                "requirement_id": REQUIREMENT_ID,
                "expectation_pointer": (
                    f"{REQUIREMENT_POINTER}/structured_expectations/{index}"
                ),
                "artifact_id": "fixture.us-consent",
                "coverage_check_state": "performed",
                "advisory_coverage_status": "DOCUMENTED",
                "document_locator": {
                    "kind": "section",
                    "value": f"Synthetic expectation {index:04d}",
                },
                "quoted_anchor_encoded": _quote(SOURCE_TEXT.strip()),
                "captured_at": CAPTURED_AT,
                "failure_state": None,
            }
        )
    _repin_profile(context, profile)
    draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": judgments,
    }
    return _case(context=context, registry=registry, draft=draft)


def test_schemas_constants_and_reason_vocabulary_are_frozen() -> None:
    row_schema = _json(ROW_SCHEMA_PATH)
    advisory_schema = _json(ADVISORY_SCHEMA_PATH)
    Draft202012Validator.check_schema(row_schema)
    Draft202012Validator.check_schema(advisory_schema)
    assert advisory_schema["additionalProperties"] is False
    assert advisory_schema["properties"]["schema_version"]["const"] == (
        "content-coverage-advisory/1.0"
    )
    assert advisory_schema["properties"]["layer"]["const"] == "LLM-ADVISORY"
    assert advisory_schema["properties"]["evaluation_status"]["const"] == "UNMEASURED"
    assert set(advisory_schema["$defs"]["reason_code"]["enum"]) == REASON_CODES
    assert coverage_runtime.DRAFT_SCHEMA_VERSION == "content-coverage-advisory-draft/1.0"
    assert coverage_runtime.REPORT_SCHEMA_VERSION == "content-coverage-advisory/1.0"
    assert coverage_runtime.LAYER == "LLM-ADVISORY"
    assert coverage_runtime.EVALUATION_STATUS == "UNMEASURED"
    assert coverage_runtime.MAX_JUDGMENTS == 4096
    assert coverage_runtime.MAX_SESSION_CONTENT_BYTES == 64 * 1024 * 1024
    assert coverage_runtime.MAX_TOTAL_SESSION_CONTENT_BYTES == 256 * 1024 * 1024
    assert coverage_runtime.MAX_ADVISORY_BYTES == 8 * 1024 * 1024
    assert coverage_runtime.MAX_RENDER_PAGE_SIZE == 25


def test_session_content_count_and_byte_bounds_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert len(coverage_runtime._validate_session_contents({f"a-{i}": "" for i in range(512)})) == 512
    with pytest.raises(ContentCoverageAdvisoryError, match="exceeds 512"):
        coverage_runtime._validate_session_contents({f"a-{i}": "" for i in range(513)})

    monkeypatch.setattr(coverage_runtime, "MAX_SESSION_CONTENT_BYTES", 4)
    assert coverage_runtime._validate_session_contents({"a": "1234"}) == {
        "a": "1234"
    }
    with pytest.raises(ContentCoverageAdvisoryError, match="64 MiB"):
        coverage_runtime._validate_session_contents({"a": "12345"})

    monkeypatch.setattr(coverage_runtime, "MAX_SESSION_CONTENT_BYTES", 8)
    monkeypatch.setattr(coverage_runtime, "MAX_TOTAL_SESSION_CONTENT_BYTES", 8)
    assert coverage_runtime._validate_session_contents({"a": "1234", "b": "5678"}) == {
        "a": "1234",
        "b": "5678",
    }
    with pytest.raises(ContentCoverageAdvisoryError, match="256 MiB total"):
        coverage_runtime._validate_session_contents({"a": "1234", "b": "56789"})


def test_public_api_is_frozen_and_packet_root_is_mandatory() -> None:
    for name in ("finalize_advisory", "validate_advisory", "render_advisory", "main"):
        assert hasattr(coverage_runtime, name)
    tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    for name in ("finalize_advisory", "validate_advisory", "render_advisory"):
        parameters = [argument.arg for argument in functions[name].args.args]
        assert "packet_root" in parameters
        assert "manifest" in parameters
        assert "session_sources" in parameters


def test_base_draft_and_final_carrier_pass_closed_schemas_and_exact_replay() -> None:
    case = _case()
    assert _draft_errors(case["draft"]) == []
    advisory = _finalize(case)
    _schema_validator().validate(advisory)
    _validate(advisory, case)
    assert advisory["report_digest"] == digest(
        {key: value for key, value in advisory.items() if key != "report_digest"}
    )


def test_live_mixed_packet_owned_and_external_seam_still_checks_packet_content() -> None:
    case = _case()
    advisory = _finalize(case)
    result = _result(advisory)
    assert result["coverage_check_state"] == "performed"
    assert result["advisory_coverage_status"] == "DOCUMENTED"
    assert result["reason_codes"] == ["ALL_EXPECTATIONS_APPEAR_COVERED"]
    assert len(result["expectation_findings"]) == 3
    refs = result["deterministic_entry_refs"]
    assert [(row["responsibility"], row["deterministic_status"]) for row in refs] == [
        ("packet_owned", "DOCUMENTED"),
        ("external_dependency", "ACCEPTANCE_UNVERIFIED"),
    ]
    assert refs[1]["matched_artifact_ids"] == []


def test_input_binding_and_deterministic_status_are_exact_copies() -> None:
    case = _case()
    advisory = _finalize(case)
    manifest = case["manifest"]
    assert advisory["input_binding"] == {
        "manifest_schema_version": manifest["schema_version"],
        "manifest_digest": manifest["manifest_digest"],
        "inventory_id": manifest["inventory_pointer"]["inventory_id"],
        "inventory_digest": manifest["inventory_pointer"]["inventory_digest"],
        "observation_digest": manifest["packet_pointer"]["observation_digest"],
        "context_record_id": manifest["authority_binding"]["context_pointer"][
            "context_record_id"
        ],
        "context_digest": manifest["authority_binding"]["context_pointer"][
            "context_digest"
        ],
        "registry_id": manifest["authority_binding"]["registry_pointer"]["registry_id"],
        "registry_version": manifest["authority_binding"]["registry_pointer"][
            "registry_version"
        ],
        "registry_as_of": manifest["authority_binding"]["registry_pointer"]["as_of"],
        "registry_digest": manifest["authority_binding"]["registry_pointer"][
            "registry_digest"
        ],
        "resolved_digest": manifest["authority_binding"]["resolved_digest"],
    }
    assert advisory["deterministic_status"] == {
        "review_pathway": manifest["administrative_status"]["review_pathway"],
        "submission_readiness": manifest["administrative_status"]["submission_readiness"],
        "authorization_status": manifest["administrative_status"]["authorization_status"],
        "review_timeline": manifest["administrative_status"]["review_timeline"],
        "acceptance_status": manifest["acceptance_boundary"]["status"],
    }
    assert advisory["boundary"] == {
        "deterministic_status_unchanged": True,
        "submission_readiness_unchanged": True,
        "authorization_status_unchanged": True,
        "institutional_acceptance_unchanged": True,
        "adequacy_not_assessed": True,
    }


def test_renderer_shows_exact_authorization_copy_independent_of_readiness() -> None:
    inventory = _inventory()
    authorization = {
        "value": "documented",
        "source_reference": "synthetic.authorization-proof",
        "provenance": "caller_supplied_no_derivation",
    }
    inventory["authorization_status_input"] = copy.deepcopy(authorization)
    complete_case = _case(inventory=inventory)
    complete = _finalize(complete_case)

    gap_inventory = copy.deepcopy(inventory)
    gap_inventory["artifacts"][0]["evidence_bindings"] = []
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    gap_case = _case(inventory=gap_inventory, draft=empty_draft, sources={})
    gap = _finalize(gap_case)

    assert complete["deterministic_status"]["authorization_status"] == authorization
    assert gap["deterministic_status"]["authorization_status"] == authorization
    assert complete["deterministic_status"]["submission_readiness"] != gap[
        "deterministic_status"
    ]["submission_readiness"]
    for advisory, case in ((complete, complete_case), (gap, gap_case)):
        rendered = _render(advisory, case)
        assert f"Authorization status: {authorization['value']}" in rendered
        assert (
            "Authorization source reference: "
            + coverage_runtime._md(authorization["source_reference"])
        ) in rendered
        assert (
            "Authorization provenance: "
            + coverage_runtime._md(authorization["provenance"])
        ) in rendered


def test_final_carrier_has_no_parallel_verdict_measurement_or_adequacy_field() -> None:
    advisory = _finalize(_case())
    forbidden = {
        "verdict",
        "adequacy",
        "approval",
        "approval_status",
        "authorization_decision",
        "compliance",
        "confidence",
        "efficacy",
        "measurement",
        "measurement_rows",
        "probability",
        "review_level",
        "score",
    }
    assert _all_keys(advisory).isdisjoint(forbidden)
    assert advisory["evaluation_status"] == "UNMEASURED"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.__setitem__("layer", "MODEL-ADVISORY"),
        lambda value: value.__setitem__("unknown", True),
        lambda value: value.pop("judgments"),
        lambda value: value["judgments"][0].__setitem__("requirement_id", REQUIREMENT_ID + "\n"),
        lambda value: value["judgments"][0].__setitem__(
            "expectation_pointer", EXPECTATION_POINTERS[0] + "\n"
        ),
        lambda value: value["judgments"][0].__setitem__("captured_at", CAPTURED_AT + "\n"),
        lambda value: value["judgments"][0].__setitem__("unexpected", "value"),
    ],
)
def test_draft_schema_and_runtime_reject_closed_or_absolute_end_mutations(
    mutate: Callable[[dict[str, Any]], Any]
) -> None:
    case = _case()
    mutate(case["draft"])
    assert _draft_errors(case["draft"])
    with pytest.raises(ContentCoverageAdvisoryError):
        _finalize(case)


@pytest.mark.parametrize(
    ("mutation", "schema_rejects"),
    [
        ("documented_empty_quote", True),
        ("documented_null_time", True),
        ("not_located_quote", True),
        ("not_located_time", True),
        ("performed_failure", False),
        ("not_checked_status", True),
        ("not_checked_quote", True),
        ("not_checked_time", True),
        ("not_checked_no_failure", True),
        ("bad_timestamp", True),
    ],
)
def test_draft_state_cross_products_fail_closed(
    mutation: str, schema_rejects: bool
) -> None:
    case = _case()
    row = case["draft"]["judgments"][0]
    if mutation == "documented_empty_quote":
        row["quoted_anchor_encoded"] = ""
    elif mutation == "documented_null_time":
        row["captured_at"] = None
    elif mutation == "not_located_quote":
        _not_located(row)
        row["quoted_anchor_encoded"] = "unexpected"
    elif mutation == "not_located_time":
        _not_located(row)
        row["captured_at"] = CAPTURED_AT
    elif mutation == "performed_failure":
        row["failure_state"] = "not_checked"
    elif mutation == "not_checked_status":
        _not_checked(row, "not_checked")
        row["advisory_coverage_status"] = "DOCUMENTED"
    elif mutation == "not_checked_quote":
        _not_checked(row, "not_checked")
        row["quoted_anchor_encoded"] = "unexpected"
    elif mutation == "not_checked_time":
        _not_checked(row, "not_checked")
        row["captured_at"] = CAPTURED_AT
    elif mutation == "not_checked_no_failure":
        _not_checked(row, "not_checked")
        row["failure_state"] = None
    else:
        row["captured_at"] = "2026-08-09T24:00:00Z"
    if schema_rejects:
        assert _draft_errors(case["draft"])
    with pytest.raises(ContentCoverageAdvisoryError):
        _finalize(case)


def test_missing_or_duplicate_expectation_accounting_fails() -> None:
    missing = _case()
    missing["draft"]["judgments"].pop()
    with pytest.raises(ContentCoverageAdvisoryError, match="missing explicit draft accounting"):
        _finalize(missing)
    duplicate = _case()
    duplicate["draft"]["judgments"].append(
        copy.deepcopy(duplicate["draft"]["judgments"][0])
    )
    with pytest.raises(ContentCoverageAdvisoryError, match="duplicates"):
        _finalize(duplicate)


@pytest.mark.parametrize("target", ["requirement", "pointer", "artifact"])
def test_unknown_or_cross_bound_draft_target_is_rejected(target: str) -> None:
    case = _case()
    row = case["draft"]["judgments"][0]
    if target == "requirement":
        row["requirement_id"] = "unknown.requirement"
    elif target == "pointer":
        row["expectation_pointer"] = (
            "/profiles/0/requirements/0/structured_expectations/0"
        )
    else:
        row["artifact_id"] = "unknown.artifact"
    with pytest.raises(ContentCoverageAdvisoryError):
        _finalize(case)


def test_aggregate_precedence_documented_not_located_conflicting_and_partial() -> None:
    documented = _finalize(_case())
    assert _result(documented)["advisory_coverage_status"] == "DOCUMENTED"

    missing_case = _case()
    _not_located(missing_case["draft"]["judgments"][1])
    not_located = _finalize(missing_case)
    assert _result(not_located)["advisory_coverage_status"] == "NOT_LOCATED"
    assert _result(not_located)["reason_codes"] == ["EXPECTATION_NOT_LOCATED"]

    conflict_case = _case()
    original = conflict_case["draft"]["judgments"][0]
    original["advisory_coverage_status"] = "CONFLICTING"
    second = copy.deepcopy(original)
    second["quoted_anchor_encoded"] = _quote("Participation is voluntary.")
    second["document_locator"]["value"] = "Consent — second passage"
    conflict_case["draft"]["judgments"].append(second)
    conflicting = _finalize(conflict_case)
    assert _result(conflicting)["advisory_coverage_status"] == "CONFLICTING"
    assert _result(conflicting)["reason_codes"] == [
        "CONFLICTING_COVERAGE_OBSERVATIONS"
    ]
    assert len(_result(conflicting)["expectation_findings"][0]["evidence_rows"]) == 2

    partial_case = _case()
    _not_checked(partial_case["draft"]["judgments"][2], "not_checked")
    partial = _finalize(partial_case)
    assert _result(partial)["coverage_check_state"] == "not_checked"
    assert _result(partial)["advisory_coverage_status"] is None
    assert "COVERAGE_CHECK_NOT_PERFORMED" in _result(partial)["reason_codes"]


@pytest.mark.parametrize("performed_status", ["DOCUMENTED", "NOT_LOCATED", "CONFLICTING"])
def test_partial_requirement_root_reports_only_unperformed_reasons(
    performed_status: str,
) -> None:
    case = _case()
    first = case["draft"]["judgments"][0]
    if performed_status == "NOT_LOCATED":
        _not_located(first)
    elif performed_status == "CONFLICTING":
        first["advisory_coverage_status"] = "CONFLICTING"
        second = copy.deepcopy(first)
        second["quoted_anchor_encoded"] = _quote("Participation is voluntary.")
        second["document_locator"]["value"] = "Consent — second passage"
        case["draft"]["judgments"].append(second)
    _not_checked(case["draft"]["judgments"][2], "not_checked")

    result = _result(_finalize(case))
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] is None
    assert result["reason_codes"] == ["COVERAGE_CHECK_NOT_PERFORMED"]
    assert set(result["reason_codes"]).isdisjoint(
        {
            "ALL_EXPECTATIONS_APPEAR_COVERED",
            "EXPECTATION_NOT_LOCATED",
            "CONFLICTING_COVERAGE_OBSERVATIONS",
        }
    )
    assert any(
        finding["advisory_coverage_status"] == performed_status
        for finding in result["expectation_findings"]
    )


@pytest.mark.parametrize("mutation", ["single", "exact_duplicate"])
def test_conflicting_requires_two_distinct_replayed_passages(mutation: str) -> None:
    case = _case()
    row = case["draft"]["judgments"][0]
    row["advisory_coverage_status"] = "CONFLICTING"
    if mutation == "exact_duplicate":
        case["draft"]["judgments"].append(copy.deepcopy(row))
    with pytest.raises(ContentCoverageAdvisoryError):
        _finalize(case)


def test_conflicting_cannot_launder_one_passage_through_percent_encoding() -> None:
    case = _case()
    first = case["draft"]["judgments"][0]
    first["advisory_coverage_status"] = "CONFLICTING"
    second = copy.deepcopy(first)
    decoded = urllib.parse.unquote(first["quoted_anchor_encoded"])
    assert decoded and first["quoted_anchor_encoded"].startswith(decoded[0])
    second["quoted_anchor_encoded"] = (
        f"%{ord(decoded[0]):02X}" + second["quoted_anchor_encoded"][1:]
    )
    assert urllib.parse.unquote(second["quoted_anchor_encoded"]) == (
        urllib.parse.unquote(first["quoted_anchor_encoded"])
    )
    case["draft"]["judgments"].append(second)
    with pytest.raises(ContentCoverageAdvisoryError, match="distinct replayed"):
        _finalize(case)


@pytest.mark.parametrize(
    ("failure_state", "reason"),
    [
        ("not_checked", "COVERAGE_CHECK_NOT_PERFORMED"),
        ("source_missing", "SESSION_CONTENT_NOT_PROVIDED"),
        ("access_failed", "SOURCE_ACCESS_FAILED"),
        ("retrieval_failed", "SOURCE_RETRIEVAL_FAILED"),
    ],
)
def test_missing_or_unavailable_content_is_not_checked_with_null_status(
    failure_state: str, reason: str
) -> None:
    case = _case(sources={})
    for judgment in case["draft"]["judgments"]:
        _not_checked(judgment, failure_state)
    advisory = _finalize(case)
    result = _result(advisory)
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] is None
    assert result["reason_codes"] == [reason]
    for finding in result["expectation_findings"]:
        assert finding["coverage_check_state"] == "not_checked"
        assert finding["advisory_coverage_status"] is None
        assert finding["reason_codes"] == [reason]
        row = finding["evidence_rows"][0]
        assert row["excerpt"]["state"] == failure_state
        assert row["source"]["source_content_sha256"] is None
        assert row["source"]["source_content_utf8_bytes"] is None
        assert row["excerpt"]["text"] is None


def test_explicit_failure_cannot_hide_content_that_was_supplied() -> None:
    for failure in ("source_missing", "access_failed", "retrieval_failed"):
        case = _case()
        for judgment in case["draft"]["judgments"]:
            _not_checked(judgment, failure)
        with pytest.raises(ContentCoverageAdvisoryError, match="contradicts"):
            _finalize(case)


def test_external_only_requirement_is_acceptance_unverified_not_missing() -> None:
    inventory = _inventory()
    inventory["packet_responsibility_role_ids"] = ["investigator"]
    case = _case(inventory=inventory, draft={
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }, sources={})
    advisory = _finalize(case)
    result = _result(advisory)
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] == "ACCEPTANCE_UNVERIFIED"
    assert result["reason_codes"] == [
        "EXTERNAL_DEPENDENCY",
        "INSTITUTIONAL_ACCEPTANCE_REQUIRED",
    ]
    assert result["expectation_findings"] == []
    assert "EXPECTATION_NOT_LOCATED" not in result["reason_codes"]


def test_profiled_waiver_route_stays_acceptance_boundary_without_false_gap() -> None:
    context, registry, _resolved, _overlay = _synthetic_overlay_authority()
    draft, sources = _synthetic_live_draft_and_sources()
    case = _case(
        inventory=_waiver_inventory(),
        packet_root=SYNTHETIC_PACKET_ROOT,
        context=context,
        registry=registry,
        draft=draft,
        sources=sources,
    )
    result = _result(_finalize(case), "synthetic.packet.base-consent")
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] == "ACCEPTANCE_UNVERIFIED"
    assert result["reason_codes"] == [
        "WAIVER_OR_EXCEPTION_BOUNDARY",
        "INSTITUTIONAL_ACCEPTANCE_REQUIRED",
    ]
    assert result["expectation_findings"] == []
    assert result["deterministic_entry_refs"][0]["deterministic_status"] == (
        "ACCEPTANCE_UNVERIFIED"
    )
    assert result["deterministic_entry_refs"][0]["matched_artifact_ids"] == []
    assert "EXPECTATION_NOT_LOCATED" not in result["reason_codes"]
    assert "DETERMINISTIC_PACKET_GAP" not in result["reason_codes"]

    targeted = copy.deepcopy(case)
    extra = copy.deepcopy(targeted["draft"]["judgments"][0])
    extra["requirement_id"] = "synthetic.packet.base-consent"
    extra["expectation_pointer"] = (
        result["requirement_ref"]["requirement_pointer"]
        + "/structured_expectations/0"
    )
    targeted["draft"]["judgments"].append(extra)
    with pytest.raises(ContentCoverageAdvisoryError, match="targets ineligible"):
        _finalize(targeted)


@pytest.mark.parametrize(
    "route_state", ["external_authority_required", "not_profiled_in_bounded_profile"]
)
def test_unprofiled_or_external_waiver_route_preserves_deterministic_gap(
    route_state: str,
) -> None:
    context, registry, _resolved, overlay = _synthetic_overlay_authority()
    base = next(
        row
        for row in overlay["requirements"]
        if row["requirement_id"] == "synthetic.packet.base-consent"
    )
    base["waiver_or_exception_route"] = {
        "state": route_state,
        "requirement_ids": [],
        "decision_maker_role": (
            "institutional_review_office"
            if route_state == "external_authority_required"
            else None
        ),
    }
    _repin_overlay(context, overlay)
    draft, sources = _synthetic_live_draft_and_sources()
    case = _case(
        inventory=_waiver_inventory(),
        packet_root=SYNTHETIC_PACKET_ROOT,
        context=context,
        registry=registry,
        draft=draft,
        sources=sources,
    )
    result = _result(_finalize(case), "synthetic.packet.base-consent")
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] is None
    assert result["reason_codes"] == ["DETERMINISTIC_PACKET_GAP"]
    assert result["expectation_findings"] == []


def test_deterministic_packet_gap_or_conflict_never_becomes_content_not_located() -> None:
    gap_inventory = _inventory()
    gap_inventory["artifacts"][0]["evidence_bindings"] = []
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    gap = _finalize(_case(inventory=gap_inventory, draft=empty_draft, sources={}))
    assert _result(gap)["advisory_coverage_status"] is None
    assert _result(gap)["reason_codes"] == ["DETERMINISTIC_PACKET_GAP"]

    conflict_inventory = _inventory()
    conflict_inventory["artifacts"][0]["declared_sha256"] = "0" * 64
    conflict = _finalize(
        _case(inventory=conflict_inventory, draft=empty_draft, sources={})
    )
    assert _result(conflict)["advisory_coverage_status"] is None
    assert _result(conflict)["reason_codes"] == [
        "DETERMINISTIC_PACKET_CONFLICT"
    ]


def test_not_located_requires_checked_no_match_for_every_eligible_artifact(
    tmp_path: Path,
) -> None:
    context = _context()
    registry = _registry()
    profile = _us_profile(registry)
    requirement = _us_requirement(registry)
    second_evidence = copy.deepcopy(requirement["evidence_expected"][0])
    second_evidence["evidence_id"] = "consent.participant-materials-second"
    requirement["evidence_expected"].append(second_evidence)
    _repin_profile(context, profile)

    packet = _packet_copy(tmp_path)
    (packet / "consent-second.txt").write_text(SOURCE_TEXT, encoding="utf-8")
    inventory = _inventory()
    second_artifact = copy.deepcopy(inventory["artifacts"][0])
    second_artifact["artifact_id"] = "fixture.us-consent-second"
    second_artifact["relative_path"] = "consent-second.txt"
    second_artifact["evidence_bindings"] = [
        {
            "requirement_id": REQUIREMENT_ID,
            "evidence_id": "consent.participant-materials-second",
        }
    ]
    inventory["artifacts"].append(second_artifact)
    draft = _draft()
    for judgment in list(draft["judgments"]):
        _not_located(judgment)
        duplicate = copy.deepcopy(judgment)
        duplicate["artifact_id"] = "fixture.us-consent-second"
        draft["judgments"].append(duplicate)
    sources = {
        "fixture.us-consent": SOURCE_TEXT,
        "fixture.us-consent-second": SOURCE_TEXT,
    }
    complete_case = _case(
        inventory=inventory,
        packet_root=packet,
        context=context,
        registry=registry,
        draft=draft,
        sources=sources,
    )
    result = _result(_finalize(complete_case))
    assert result["coverage_check_state"] == "performed"
    assert result["advisory_coverage_status"] == "NOT_LOCATED"
    assert result["reason_codes"] == ["EXPECTATION_NOT_LOCATED"]
    assert all(
        {row["source"]["artifact_id"] for row in finding["evidence_rows"]}
        == {"fixture.us-consent", "fixture.us-consent-second"}
        for finding in result["expectation_findings"]
    )

    partial = copy.deepcopy(complete_case)
    partial["draft"]["judgments"].pop()
    with pytest.raises(ContentCoverageAdvisoryError, match="every eligible artifact"):
        _finalize(partial)


def test_conditional_false_is_copied_only_as_excluded_and_renderer_is_neutral() -> None:
    context = _context()
    registry = _registry()
    profile = _us_profile(registry)
    requirement = _us_requirement(registry)
    requirement["applies_if"] = {
        "op": "fact_equals",
        "fact_id": "packet_v1.non_clinical",
        "value": False,
    }
    _repin_profile(context, profile)
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    case = _case(context=context, registry=registry, draft=empty_draft, sources={})
    advisory = _finalize(case)
    assert advisory["requirement_results"] == []
    assert len(advisory["excluded_requirements"]) == 1
    excluded = advisory["excluded_requirements"][0]
    assert excluded["requirement_ref"]["requirement_id"] == REQUIREMENT_ID
    assert excluded["requirement_ref"]["requirement_pointer"] == REQUIREMENT_POINTER
    assert excluded["exclusion_basis"] == "resolved_predicate_false"
    rendered = _render(advisory, case)
    assert "APPLICABILITY_UNRESOLVED" not in rendered
    assert coverage_runtime._md(REQUIREMENT_ID) in rendered
    assert coverage_runtime._md(REQUIREMENT_POINTER) in rendered
    assert r"resolved\_predicate\_false" not in rendered  # renderer uses entities
    assert "resolved&#95;predicate&#95;false" in rendered
    assert "no applicable advisory requirement results" in rendered


def test_unprovided_overlay_marks_each_base_requirement_applicability_unresolved() -> None:
    context = _context()
    context["overlay_selection_state"]["institutional"] = "not_provided"
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    case = _case(context=context, draft=empty_draft, sources={})
    assert case["manifest"]["entries"]
    assert case["manifest"]["unresolved_reasons"] == [
        {
            "status": "APPLICABILITY_UNRESOLVED",
            "code": "OVERLAY_SELECTION_NOT_PROVIDED",
            "fact_id": None,
            "overlay_kind": "institutional",
        }
    ]

    class BombMapping(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError("overlay-unresolved flow consumed session content")

        def __iter__(self):
            raise AssertionError("overlay-unresolved flow consumed session content")

        def __len__(self) -> int:
            raise AssertionError("overlay-unresolved flow consumed session content")

    case["sources"] = BombMapping()
    advisory = _finalize(case)
    result = _result(advisory)
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] == "APPLICABILITY_UNRESOLVED"
    assert result["reason_codes"] == ["APPLICABILITY_UNRESOLVED"]
    assert result["expectation_findings"] == []
    assert "SESSION_CONTENT_NOT_PROVIDED" not in result["reason_codes"]
    assert "ALL_EXPECTATIONS_APPEAR_COVERED" not in result["reason_codes"]

    targeted = copy.deepcopy(case)
    targeted["draft"] = _draft()
    targeted["sources"] = {}
    with pytest.raises(ContentCoverageAdvisoryError, match="targets ineligible"):
        _finalize(targeted)


def test_closed_capability_gate_fails_before_draft_or_content_consumption() -> None:
    context = _context()
    context["declared_facts"] = [
        row
        for row in context["declared_facts"]
        if row["fact_id"] != "packet_v1.non_clinical"
    ]
    case = _case(context=context, draft={}, sources={})
    assert case["manifest"]["capability_envelope"]["state"] == "unresolved"
    assert case["manifest"]["entries"] == []

    class BombMapping(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError("closed gate consumed session content")

        def __iter__(self):
            raise AssertionError("closed gate consumed session content")

        def __len__(self) -> int:
            raise AssertionError("closed gate consumed session content")

    case["draft"] = {"explode_if_consumed": object()}
    case["sources"] = BombMapping()
    with pytest.raises(
        ContentCoverageAdvisoryError, match="manifest.capability_envelope"
    ):
        _finalize(case)


def test_no_profiled_expectations_is_not_checked_never_covered() -> None:
    context = _context()
    registry = _registry()
    profile = _us_profile(registry)
    _us_requirement(registry)["structured_expectations"] = []
    _repin_profile(context, profile)
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    advisory = _finalize(
        _case(context=context, registry=registry, draft=empty_draft)
    )
    result = _result(advisory)
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] is None
    assert result["reason_codes"] == ["NO_PROFILED_STRUCTURED_EXPECTATIONS"]
    assert result["expectation_findings"] == []


def test_resolved_empty_surface_renders_neutral_none_without_applicability_claim() -> None:
    context = _context()
    registry = _registry()
    profile = _us_profile(registry)
    requirement = _us_requirement(registry)
    requirement["consumer_scopes"] = [
        scope for scope in requirement["consumer_scopes"] if scope != "submission_packet"
    ]
    _repin_profile(context, profile)
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    case = _case(context=context, registry=registry, draft=empty_draft, sources={})
    advisory = _finalize(case)
    assert advisory["requirement_results"] == []
    assert advisory["excluded_requirements"] == []
    rendered = _render(advisory, case)
    assert "no applicable advisory requirement results" in rendered
    assert "APPLICABILITY_UNRESOLVED" not in rendered
    assert "EXPECTATION_NOT_LOCATED" not in rendered


def test_confirmed_at_reconfirmation_does_not_change_advisory_timestamp_or_digest() -> None:
    baseline_case = _case()
    baseline = _finalize(baseline_case)
    context = copy.deepcopy(baseline_case["context"])
    context["confirmed_at"] = "2026-08-09T15:45:00+08:00"
    replay_case = _case(context=context)
    after = _finalize(replay_case)
    assert after == baseline
    timestamps = {
        row["excerpt"]["captured_at"]
        for result in after["requirement_results"]
        for finding in result["expectation_findings"]
        for row in finding["evidence_rows"]
    }
    assert timestamps == {CAPTURED_AT}


def test_draft_judgment_and_json_key_order_do_not_change_bytes() -> None:
    case = _case()
    baseline = _finalize(case)
    reordered = copy.deepcopy(case)
    reordered["draft"] = json.loads(
        json.dumps(reordered["draft"], ensure_ascii=False, sort_keys=True)
    )
    reordered["draft"]["judgments"].reverse()
    assert _finalize(reordered) == baseline


def test_same_artifact_conflict_observation_permutation_is_byte_identical() -> None:
    case = _case()
    first = case["draft"]["judgments"][0]
    first["advisory_coverage_status"] = "CONFLICTING"
    second = copy.deepcopy(first)
    second["quoted_anchor_encoded"] = _quote("Participation is voluntary.")
    second["document_locator"]["value"] = "Consent — second passage"
    case["draft"]["judgments"].append(second)
    baseline = _finalize(case)

    permuted = copy.deepcopy(case)
    permuted["draft"] = {
        key: permuted["draft"][key]
        for key in reversed(tuple(permuted["draft"]))
    }
    permuted["draft"]["judgments"] = [
        {key: row[key] for key in reversed(tuple(row))}
        for row in reversed(permuted["draft"]["judgments"])
    ]
    after = _finalize(permuted)
    assert after == baseline
    assert _canonical_bytes(after) == _canonical_bytes(baseline)


def test_manifest_replay_failure_happens_before_draft_or_content_consumption() -> None:
    case = _case()
    case["manifest"]["entries"][0]["matched_artifact_ids"] = []
    _repin_report(case["manifest"])

    class BombMapping(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError("content consumed before replay")

        def __iter__(self):
            raise AssertionError("content consumed before replay")

        def __len__(self) -> int:
            raise AssertionError("content consumed before replay")

    case["draft"] = {"explode_if_consumed": object()}
    case["sources"] = BombMapping()
    with pytest.raises(ContentCoverageAdvisoryError, match="manifest replay"):
        _finalize(case)


@pytest.mark.parametrize(
    "mutation",
    [
        "layer",
        "evaluation",
        "input_digest",
        "deterministic_readiness",
        "entry_status",
        "requirement_pointer",
        "expectation_digest",
        "evidence_span",
        "boundary",
    ],
)
def test_resigned_final_advisory_mutations_fail_exact_replay(mutation: str) -> None:
    case = _case()
    advisory = _finalize(case)
    result = _result(advisory)
    if mutation == "layer":
        advisory["layer"] = "MODEL-ADVISORY"
    elif mutation == "evaluation":
        advisory["evaluation_status"] = "MEASURED"
    elif mutation == "input_digest":
        advisory["input_binding"]["manifest_digest"] = "0" * 64
    elif mutation == "deterministic_readiness":
        advisory["deterministic_status"]["submission_readiness"] = "gaps_located"
    elif mutation == "entry_status":
        result["deterministic_entry_refs"][0]["deterministic_status"] = "NOT_LOCATED"
    elif mutation == "requirement_pointer":
        result["requirement_ref"]["requirement_pointer"] = "/profiles/0/requirements/0"
    elif mutation == "expectation_digest":
        result["expectation_findings"][0]["expectation_ref"]["expectation_digest"] = "0" * 64
    elif mutation == "evidence_span":
        evidence = result["expectation_findings"][0]["evidence_rows"][0]
        evidence["excerpt"]["source_span_utf8"]["start"] += 1
        evidence["row_sha256"] = digest(
            {key: value for key, value in evidence.items() if key != "row_sha256"}
        )
    else:
        advisory["boundary"]["authorization_status_unchanged"] = False
    _repin_report(advisory)
    with pytest.raises(ContentCoverageAdvisoryError):
        _validate(advisory, case)


def test_unknown_session_source_is_rejected_without_ambient_lookup() -> None:
    case = _case()
    case["sources"]["unknown.artifact"] = "sentinel"
    with pytest.raises(ContentCoverageAdvisoryError, match="unknown artifact"):
        _finalize(case)


@pytest.mark.parametrize("mutation", ["lying_length", "duplicate_items"])
def test_adversarial_session_mapping_cannot_bypass_bounds_or_overwrite(
    mutation: str,
) -> None:
    case = _case()
    if mutation == "lying_length":
        pairs = [(f"synthetic.artifact-{index}", "x") for index in range(513)]
        expected = "exceeds 512"
    else:
        pairs = [
            ("fixture.us-consent", SOURCE_TEXT),
            ("fixture.us-consent", "attacker overwrite"),
        ]
        expected = "duplicate"

    class AdversarialMapping(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            for candidate, value in pairs:
                if candidate == key:
                    return value
            raise KeyError(key)

        def __iter__(self):
            return iter(())

        def __len__(self) -> int:
            return 0

        def items(self):
            return iter(pairs)

    case["sources"] = AdversarialMapping()
    with pytest.raises(ContentCoverageAdvisoryError, match=expected):
        _finalize(case)


def test_runtime_has_no_model_network_process_or_ambient_scan() -> None:
    tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
    forbidden_imports = {"anthropic", "http", "openai", "requests", "socket", "subprocess"}
    forbidden_calls = {
        "fwalk",
        "glob",
        "iglob",
        "iterdir",
        "listdir",
        "rglob",
        "scandir",
        "walk",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".", 1)[0] not in forbidden_imports for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert not node.module.startswith("urllib.request")
        elif isinstance(node, ast.Call):
            name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else None
            )
            assert name not in forbidden_calls


def test_in_process_finalize_and_render_never_open_a_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    case = _case()
    advisory = _finalize(case)
    assert "LLM-ADVISORY" in _render(advisory, case)


def test_renderer_escapes_locator_and_excerpt_injection(tmp_path: Path) -> None:
    packet = _packet_copy(tmp_path)
    inventory = _inventory()
    injected = (
        "<script>alert(1)</script> | [click](https://example.invalid) "
        "![x](javascript:alert(2))"
    )
    text = f"{injected}\n"
    _set_packet_text(packet, inventory, text)
    draft = _draft()
    for index, judgment in enumerate(draft["judgments"]):
        judgment["quoted_anchor_encoded"] = _quote(injected)
        judgment["document_locator"]["value"] = (
            f"<img src=x onerror=alert({index})> | [link](https://example.invalid)"
        )
    case = _case(
        inventory=inventory,
        packet_root=packet,
        draft=draft,
        sources={"fixture.us-consent": text},
    )
    advisory = _finalize(case)
    rendered = _render(advisory, case)
    for unsafe in (
        "<script>",
        "</script>",
        "<img",
        "](https://",
        "javascript:",
        " | [",
    ):
        assert unsafe not in rendered
    assert "&lt;script&gt;" in rendered
    assert "LLM-ADVISORY" in rendered
    assert "UNMEASURED" in rendered


@pytest.mark.parametrize("field", ["locator", "quote"])
def test_bidi_and_line_injection_are_rejected(field: str) -> None:
    case = _case()
    if field == "locator":
        case["draft"]["judgments"][0]["document_locator"]["value"] = "safe\u202eevil"
    else:
        case["draft"]["judgments"][0]["quoted_anchor_encoded"] = _quote("safe\nrow")
    with pytest.raises(ContentCoverageAdvisoryError):
        _finalize(case)


def test_advisory_byte_limit_is_inclusive_and_applies_to_build_validate_render(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _case()
    baseline = _finalize(case)
    exact_size = len(_canonical_bytes(baseline))
    monkeypatch.setattr(coverage_runtime, "MAX_ADVISORY_BYTES", exact_size)
    at_limit = _finalize(case)
    _validate(at_limit, case)
    assert "LLM-ADVISORY" in _render(at_limit, case)
    monkeypatch.setattr(coverage_runtime, "MAX_ADVISORY_BYTES", exact_size - 1)
    with pytest.raises(ContentCoverageAdvisoryError, match="exceeds"):
        _finalize(case)
    with pytest.raises(ContentCoverageAdvisoryError, match="exceeds"):
        _validate(baseline, case)
    with pytest.raises(ContentCoverageAdvisoryError, match="exceeds"):
        _render(baseline, case)


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 25), (1, 0), (1, 26), (2, 25), (True, 25), (1, True)],
)
def test_renderer_rejects_invalid_page_or_size(page: Any, page_size: Any) -> None:
    case = _case()
    advisory = _finalize(case)
    with pytest.raises(ValueError):
        _render(advisory, case, page=page, page_size=page_size)


def test_renderer_emits_one_bounded_page_with_navigation() -> None:
    case = _case()
    advisory = _finalize(case)
    rendered = _render(advisory, case, page=1, page_size=2)
    assert "Page 1/2" in rendered
    assert "Previous page none; Next page 2" in rendered
    assert "EVR\\-CC\\-000001" in rendered
    assert "EVR\\-CC\\-000002" in rendered
    assert "EVR\\-CC\\-000003" not in rendered
    second = _render(advisory, case, page=2, page_size=2)
    assert "Page 2/2" in second
    assert "Previous page 1; Next page none" in second
    assert "EVR\\-CC\\-000003" in second
    assert "EVR\\-CC\\-000001" not in second


@pytest.mark.parametrize("count", [0, 1, 25, 26])
def test_renderer_paging_boundaries_preserve_all_rows_once(count: int) -> None:
    case = _expectation_count_case(count)
    advisory = _finalize(case)
    rows = [
        row
        for result in advisory["requirement_results"]
        for finding in result["expectation_findings"]
        for row in finding["evidence_rows"]
    ]
    assert len(rows) == count
    assert [row["row_id"] for row in rows] == [
        f"EVR-CC-{index:06d}" for index in range(1, count + 1)
    ]
    pages = max(1, (count + 24) // 25)
    observed: list[str] = []
    for page in range(1, pages + 1):
        rendered = _render(advisory, case, page=page)
        page_rows = [
            token.replace("\\-", "-")
            for token in re.findall(r"EVR\\-CC\\-[0-9]{6}", rendered)
        ]
        assert len(page_rows) <= 25
        observed.extend(page_rows)
        if count:
            assert f"Page {page}/{pages}" in rendered
    assert observed == [row["row_id"] for row in rows]


def test_one_thousand_one_rows_traverse_without_loss_reorder_or_all_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _expectation_count_case(1001)
    advisory = _finalize(case)
    _validate(advisory, case)
    expected = [f"EVR-CC-{index:06d}" for index in range(1, 1002)]
    persisted = [
        row["row_id"]
        for result in advisory["requirement_results"]
        for finding in result["expectation_findings"]
        for row in finding["evidence_rows"]
    ]
    assert persisted == expected

    # Exact replay was exercised above. Keep page traversal focused on the
    # renderer/paginator rather than rebuilding the same 1001-row carrier 41 times.
    monkeypatch.setattr(coverage_runtime, "validate_advisory", lambda *_args, **_kwargs: None)
    for page, page_expected in (
        (1, expected[:25]),
        (41, expected[1000:]),
    ):
        rendered = _render(advisory, case, page=page)
        page_rows = [
            token.replace("\\-", "-")
            for token in re.findall(r"EVR\\-CC\\-[0-9]{6}", rendered)
        ]
        assert page_rows == page_expected
        assert f"Page {page}/41" in rendered

    calls: list[tuple[int, int, int]] = []

    def fast_bounded_renderer(
        rows: list[dict[str, Any]],
        *,
        page: int,
        page_size: int,
        session_sources: Mapping[str, str],
    ) -> str:
        del session_sources
        calls.append((len(rows), page, page_size))
        start = (page - 1) * page_size
        if start >= len(rows):
            raise ValueError("page outside full carrier")
        selected = rows[start : start + page_size]
        return "\n".join(row["row_id"].replace("-", "\\-") for row in selected)

    monkeypatch.setattr(
        coverage_runtime, "render_evidence_rows_markdown", fast_bounded_renderer
    )
    observed: list[str] = []
    for page in range(1, 42):
        rendered = _render(advisory, case, page=page)
        page_rows = [
            token.replace("\\-", "-")
            for token in re.findall(r"EVR\\-CC\\-[0-9]{6}", rendered)
        ]
        assert 1 <= len(page_rows) <= 25
        observed.extend(page_rows)
    assert observed == expected
    assert calls == [(1001, page, 25) for page in range(1, 42)]
    with pytest.raises(ValueError):
        _render(advisory, case, page=42)


def _cli_case(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    case = _case()
    advisory = _finalize(case)
    paths = {
        name: tmp_path / f"{name}.json"
        for name in (
            "draft",
            "inventory",
            "context",
            "registry",
            "resolved",
            "manifest",
            "sources",
            "advisory",
        )
    }
    for name in paths:
        value = advisory if name == "advisory" else case[name]
        _write_json(paths[name], value)
    paths["built"] = tmp_path / "built.json"
    paths["rendered"] = tmp_path / "rendered.md"
    return case, paths


def _cli_common(paths: dict[str, Path]) -> list[str]:
    return [
        "--draft",
        str(paths["draft"]),
        "--inventory",
        str(paths["inventory"]),
        "--packet-root",
        str(PACKET_ROOT),
        "--context",
        str(paths["context"]),
        "--registry",
        str(paths["registry"]),
        "--resolved",
        str(paths["resolved"]),
        "--manifest",
        str(paths["manifest"]),
        "--source-map",
        str(paths["sources"]),
    ]


def test_cli_build_validate_render_require_full_named_replay(tmp_path: Path) -> None:
    _case_value, paths = _cli_case(tmp_path)
    common = _cli_common(paths)
    assert main(["build", *common, "--output", str(paths["built"])]) == 0
    assert _json(paths["built"]) == _json(paths["advisory"])
    assert paths["built"].read_bytes() == _canonical_bytes(_json(paths["advisory"]))
    assert not paths["built"].read_bytes().endswith(b"\n")
    assert main(["validate", *common, "--advisory", str(paths["built"])]) == 0
    assert (
        main(
            [
                "render",
                *common,
                "--advisory",
                str(paths["built"]),
                "--output",
                str(paths["rendered"]),
            ]
        )
        == 0
    )
    rendered = paths["rendered"].read_text(encoding="utf-8")
    assert "LLM-ADVISORY" in rendered
    assert "UNMEASURED" in rendered


def test_cli_closed_gate_fails_before_opening_draft_or_source_map(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    context = _context()
    context["declared_facts"] = [
        row
        for row in context["declared_facts"]
        if row["fact_id"] != "packet_v1.non_clinical"
    ]
    closed = _case(context=context, draft={}, sources={})
    _case_value, paths = _cli_case(tmp_path)
    for name in ("context", "resolved", "manifest"):
        _write_json(paths[name], closed[name])
    paths["draft"] = tmp_path / "must-not-open-draft.json"
    paths["sources"] = tmp_path / "must-not-open-source-map.json"

    assert main(["build", *_cli_common(paths)]) == 2
    error = capsys.readouterr().err
    assert "manifest.capability_envelope" in error
    assert "must-not-open" not in error


def test_cli_overlay_unresolved_does_not_open_source_map(tmp_path: Path) -> None:
    context = _context()
    context["overlay_selection_state"]["institutional"] = "not_provided"
    empty_draft = {
        "schema_version": "content-coverage-advisory-draft/1.0",
        "layer": "LLM-ADVISORY",
        "judgments": [],
    }
    unresolved = _case(context=context, draft=empty_draft, sources={})
    _case_value, paths = _cli_case(tmp_path)
    for name in ("draft", "context", "resolved", "manifest"):
        _write_json(paths[name], unresolved[name])
    paths["sources"] = tmp_path / "must-not-open-source-map.json"

    assert main(["build", *_cli_common(paths), "--output", str(paths["built"])]) == 0
    result = _result(_json(paths["built"]))
    assert result["coverage_check_state"] == "not_checked"
    assert result["advisory_coverage_status"] == "APPLICABILITY_UNRESOLVED"
    assert result["reason_codes"] == ["APPLICABILITY_UNRESOLVED"]
    assert result["expectation_findings"] == []


@pytest.mark.parametrize(
    ("target", "payload"),
    [
        ("draft", '{"layer":"a","layer":"b"}'),
        ("inventory", '{"schema_version":"a","schema_version":"b"}'),
        ("context", '{"value":NaN}'),
        ("registry", '{"value":Infinity}'),
        ("resolved", '{"value":-Infinity}'),
        ("manifest", '{"schema_version":"a","schema_version":"b"}'),
        ("sources", '{"fixture.us-consent":"a","fixture.us-consent":"b"}'),
        ("advisory", '{"layer":"a","layer":"b"}'),
    ],
)
def test_cli_rejects_duplicate_or_nonfinite_named_json(
    tmp_path: Path, target: str, payload: str
) -> None:
    _case_value, paths = _cli_case(tmp_path)
    paths[target].write_text(payload, encoding="utf-8")
    command = "validate" if target == "advisory" else "build"
    argv = [command, *_cli_common(paths)]
    if command == "validate":
        argv.extend(["--advisory", str(paths["advisory"])])
    assert main(argv) == 2


def test_cli_rejects_abbreviations_all_pages_and_missing_packet_root(
    tmp_path: Path,
) -> None:
    _case_value, paths = _cli_case(tmp_path)
    common = _cli_common(paths)
    with pytest.raises(SystemExit) as abbreviated:
        main(["build", "--dra", str(paths["draft"])])
    assert abbreviated.value.code == 2
    with pytest.raises(SystemExit) as unbounded:
        main(
            [
                "render",
                *common,
                "--advisory",
                str(paths["advisory"]),
                "--all",
            ]
        )
    assert unbounded.value.code == 2
    without_root = common[:]
    root_index = without_root.index("--packet-root")
    del without_root[root_index : root_index + 2]
    with pytest.raises(SystemExit) as missing:
        main(["build", *without_root])
    assert missing.value.code == 2


def test_cli_render_rejects_resigned_but_forged_advisory(tmp_path: Path) -> None:
    _case_value, paths = _cli_case(tmp_path)
    forged = _json(paths["advisory"])
    forged["requirement_results"][0]["advisory_coverage_status"] = "NOT_LOCATED"
    _repin_report(forged)
    _write_json(paths["advisory"], forged)
    assert (
        main(
            [
                "render",
                *_cli_common(paths),
                "--advisory",
                str(paths["advisory"]),
            ]
        )
        == 2
    )


def test_cli_subprocess_does_not_offer_unbounded_all_option(tmp_path: Path) -> None:
    _case_value, paths = _cli_case(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(RUNTIME_PATH),
            "render",
            *_cli_common(paths),
            "--advisory",
            str(paths["advisory"]),
            "--all",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--all" in result.stderr
