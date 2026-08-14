#!/usr/bin/env python3
"""Finalize, replay-validate, and render the bounded #681 LLM advisory.

The runtime consumes evaluator judgments only as explicit input.  It performs no
model call, prose classification, retrieval, directory scan, or ambient source
lookup.  Every authority and packet pointer is re-established from the complete
#666/#667 named input set before it is copied into the advisory carrier.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NoReturn

try:  # Direct execution puts scripts/ on sys.path.
    from build_submission_packet_manifest import validate_submission_packet_manifest
    from evidence_rows import (
        ADVISORY_SCHEMA_VERSION,
        ADVISORY_SURFACE,
        DOCUMENT_LOCATOR_PROVENANCE,
        EvidenceRowError,
        build_advisory,
        render_markdown as render_evidence_rows_markdown,
        strict_percent_decode,
    )
    from resolve_human_subjects_authority import ContractError, digest, load_json
except ModuleNotFoundError:  # Package-style imports used by some test runners.
    from scripts.build_submission_packet_manifest import (  # type: ignore[no-redef]
        validate_submission_packet_manifest,
    )
    from scripts.evidence_rows import (  # type: ignore[no-redef]
        ADVISORY_SCHEMA_VERSION,
        ADVISORY_SURFACE,
        DOCUMENT_LOCATOR_PROVENANCE,
        EvidenceRowError,
        build_advisory,
        render_markdown as render_evidence_rows_markdown,
        strict_percent_decode,
    )
    from scripts.resolve_human_subjects_authority import (  # type: ignore[no-redef]
        ContractError,
        digest,
        load_json,
    )


DRAFT_SCHEMA_VERSION = "content-coverage-advisory-draft/1.0"
REPORT_SCHEMA_VERSION = "content-coverage-advisory/1.0"
LAYER = "LLM-ADVISORY"
EVALUATION_STATUS = "UNMEASURED"
MAX_JUDGMENTS = 4096
MAX_SESSION_CONTENT_BYTES = 64 * 1024 * 1024
MAX_TOTAL_SESSION_CONTENT_BYTES = 256 * 1024 * 1024
MAX_ADVISORY_BYTES = 8 * 1024 * 1024
MAX_RENDER_PAGE_SIZE = 25

PERFORMED_STATUSES = frozenset({"DOCUMENTED", "NOT_LOCATED", "CONFLICTING"})
ADVISORY_STATUSES = frozenset(
    {
        "DOCUMENTED",
        "NOT_LOCATED",
        "CONFLICTING",
        "APPLICABILITY_UNRESOLVED",
        "ACCEPTANCE_UNVERIFIED",
    }
)
FAILURE_STATES = frozenset(
    {"not_checked", "source_missing", "access_failed", "retrieval_failed"}
)
LOCATOR_KINDS = frozenset({"document", "page", "section", "paragraph", "other"})
REASON_CODES = frozenset(
    {
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
)
_RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt]"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$"
)
FAILURE_REASON = {
    "not_checked": "COVERAGE_CHECK_NOT_PERFORMED",
    "source_missing": "SESSION_CONTENT_NOT_PROVIDED",
    "access_failed": "SOURCE_ACCESS_FAILED",
    "retrieval_failed": "SOURCE_RETRIEVAL_FAILED",
}
STATUS_REASON = {
    "DOCUMENTED": "ALL_EXPECTATIONS_APPEAR_COVERED",
    "NOT_LOCATED": "EXPECTATION_NOT_LOCATED",
    "CONFLICTING": "CONFLICTING_COVERAGE_OBSERVATIONS",
}


class ContentCoverageAdvisoryError(ValueError):
    """A #681 draft, binding, or report violates the frozen contract."""


class ContentCoverageAdvisoryInputError(ContentCoverageAdvisoryError):
    """A named CLI input could not be loaded as a supported strict value."""


def _fail(path: str, message: str) -> NoReturn:
    raise ContentCoverageAdvisoryError(f"{path}: {message}")


def _closed(value: Any, path: str, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    missing = fields - set(value)
    extra = set(value) - fields
    if missing:
        _fail(path, f"missing field(s): {', '.join(sorted(missing))}")
    if extra:
        _fail(path, f"undeclared field(s): {', '.join(sorted(extra))}")
    return value


def _array(value: Any, path: str, *, maximum: int = MAX_JUDGMENTS) -> list[Any]:
    if not isinstance(value, list):
        _fail(path, "must be an array")
    if len(value) > maximum:
        _fail(path, f"exceeds {maximum} items")
    return value


def _text(value: Any, path: str, *, maximum: int = 1000, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value):
        _fail(path, "must be a string" + ("" if empty else " with at least one character"))
    if len(value) > maximum:
        _fail(path, f"must not exceed {maximum} characters")
    for character in value:
        code = ord(character)
        if code == 127 or code < 32 or 0xD800 <= code <= 0xDFFF:
            _fail(path, "contains a forbidden control or surrogate character")
        if unicodedata.category(character) in {"Cf", "Zl", "Zp"}:
            _fail(path, "contains a forbidden format or line-separator character")
    return value


def _identifier(value: Any, path: str) -> str:
    text = _text(value, path, maximum=200)
    if not text[0].isalnum() or not text[0].isascii() or not all(
        character.isascii()
        and (character.islower() or character.isdigit() or character in "._-")
        for character in text
    ):
        _fail(path, "must use lowercase ASCII letters, digits, dot, underscore, or hyphen")
    return text


def _enum(value: Any, path: str, choices: frozenset[str] | set[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        _fail(path, f"must be one of {sorted(choices)}")
    return value


def _timestamp(value: Any, path: str) -> str:
    text = _text(value, path, maximum=100)
    if _RFC3339_RE.fullmatch(text) is None:
        _fail(path, "must be an RFC 3339 date-time with an offset")
    candidate = text[:-1] + "+00:00" if text[-1] in {"Z", "z"} else text
    try:
        dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        _fail(path, f"must be a real RFC 3339 date-time: {exc}")
    return text


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        _fail("value", f"cannot be serialized canonically: {exc}")


def _enforce_advisory_byte_limit(value: Any) -> None:
    size = len(_canonical_bytes(value))
    if size > MAX_ADVISORY_BYTES:
        _fail("advisory", f"canonical carrier exceeds {MAX_ADVISORY_BYTES} bytes")


def _pointer_get(root: dict[str, Any], pointer: str, path: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        _fail(path, "must be an absolute JSON Pointer")
    current: Any = root
    for token in pointer[1:].split("/"):
        if "~" in token:
            token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                _fail(path, "contains an invalid array index")
            index = int(token)
            if index >= len(current):
                _fail(path, "does not resolve")
            current = current[index]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            _fail(path, "does not resolve")
    return current


def _validate_session_contents(value: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        _fail("session_contents", "must be an artifact_id-to-text mapping")
    result: dict[str, str] = {}
    total = 0
    for count, (key, content) in enumerate(value.items(), start=1):
        if count > 512:
            _fail("session_contents", "exceeds 512 explicitly supplied artifacts")
        artifact_id = _identifier(key, "session_contents key")
        if artifact_id in result:
            _fail(
                f"session_contents.{artifact_id}",
                "duplicates an earlier explicitly supplied artifact",
            )
        if not isinstance(content, str):
            _fail(f"session_contents.{artifact_id}", "must be a string")
        try:
            size = len(content.encode("utf-8", errors="strict"))
        except UnicodeError as exc:
            _fail(f"session_contents.{artifact_id}", f"is not strict UTF-8: {exc}")
        if size > MAX_SESSION_CONTENT_BYTES:
            _fail(f"session_contents.{artifact_id}", "exceeds 64 MiB")
        total += size
        if total > MAX_TOTAL_SESSION_CONTENT_BYTES:
            _fail("session_contents", "exceeds 256 MiB total")
        result[artifact_id] = content
    return result


def _validate_draft(draft: dict[str, Any]) -> list[dict[str, Any]]:
    root = _closed(draft, "draft", {"schema_version", "layer", "judgments"})
    if root["schema_version"] != DRAFT_SCHEMA_VERSION:
        _fail("draft.schema_version", f"must equal {DRAFT_SCHEMA_VERSION}")
    if root["layer"] != LAYER:
        _fail("draft.layer", f"must equal {LAYER}")
    judgments: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    fields = {
        "requirement_id",
        "expectation_pointer",
        "artifact_id",
        "coverage_check_state",
        "advisory_coverage_status",
        "document_locator",
        "quoted_anchor_encoded",
        "failure_state",
        "captured_at",
    }
    for index, raw in enumerate(_array(root["judgments"], "draft.judgments")):
        path = f"draft.judgments[{index}]"
        row = _closed(raw, path, fields)
        requirement_id = _identifier(row["requirement_id"], f"{path}.requirement_id")
        expectation_pointer = _text(
            row["expectation_pointer"], f"{path}.expectation_pointer", maximum=2000
        )
        artifact_id = _identifier(row["artifact_id"], f"{path}.artifact_id")
        check_state = _enum(
            row["coverage_check_state"],
            f"{path}.coverage_check_state",
            frozenset({"performed", "not_checked"}),
        )
        locator = _closed(row["document_locator"], f"{path}.document_locator", {"kind", "value"})
        normalized_locator = {
            "kind": _enum(locator["kind"], f"{path}.document_locator.kind", LOCATOR_KINDS),
            "value": _text(locator["value"], f"{path}.document_locator.value", maximum=500),
        }
        encoded = _text(
            row["quoted_anchor_encoded"],
            f"{path}.quoted_anchor_encoded",
            maximum=12000,
            empty=True,
        )
        try:
            decoded = strict_percent_decode(encoded)
        except EvidenceRowError as exc:
            _fail(f"{path}.quoted_anchor_encoded", str(exc))
        status = row["advisory_coverage_status"]
        failure = row["failure_state"]
        captured_at = row["captured_at"]
        if check_state == "performed":
            status = _enum(status, f"{path}.advisory_coverage_status", PERFORMED_STATUSES)
            if failure is not None:
                _fail(f"{path}.failure_state", "must be null when coverage_check_state=performed")
            if status in {"DOCUMENTED", "CONFLICTING"} and not decoded:
                _fail(f"{path}.quoted_anchor_encoded", f"status={status} requires a quote")
            if status == "NOT_LOCATED" and decoded:
                _fail(f"{path}.quoted_anchor_encoded", "NOT_LOCATED requires an empty anchor")
            if status in {"DOCUMENTED", "CONFLICTING"}:
                captured_at = _timestamp(captured_at, f"{path}.captured_at")
            elif captured_at is not None:
                _fail(f"{path}.captured_at", "NOT_LOCATED requires null")
        else:
            if status is not None:
                _fail(f"{path}.advisory_coverage_status", "must be null when not_checked")
            failure = _enum(failure, f"{path}.failure_state", FAILURE_STATES)
            if decoded:
                _fail(f"{path}.quoted_anchor_encoded", "not_checked requires an empty anchor")
            if captured_at is not None:
                _fail(f"{path}.captured_at", "not_checked requires null")
        normalized = {
                "requirement_id": requirement_id,
                "expectation_pointer": expectation_pointer,
                "artifact_id": artifact_id,
                "coverage_check_state": check_state,
                "advisory_coverage_status": status,
                "document_locator": normalized_locator,
                "quoted_anchor_encoded": encoded,
                "failure_state": failure,
                "captured_at": captured_at,
            }
        identity = (
            requirement_id,
            expectation_pointer,
            artifact_id,
            check_state,
            status,
            normalized_locator["kind"],
            normalized_locator["value"],
            encoded,
            failure,
            captured_at,
        )
        if identity in seen:
            _fail(path, "duplicates an earlier exact coverage observation")
        seen.add(identity)
        judgments.append(normalized)
    return judgments


def _manifest_entry_ref(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_ref": copy.deepcopy(entry["evidence_ref"]),
        "responsibility": entry["responsibility"],
        "deterministic_status": entry["status"],
        "reason_codes": copy.deepcopy(entry["reason_codes"]),
        "matched_artifact_ids": copy.deepcopy(entry["matched_artifact_ids"]),
    }


def _authority_anchor_ref(requirement: dict[str, Any], pointer: str) -> dict[str, Any]:
    anchor = requirement["authority_anchor"]
    return {
        "authority_anchor_pointer": pointer + "/authority_anchor",
        "authority_anchor_digest": digest(anchor),
        "source_id": anchor["source_id"],
        "provision": anchor["provision"],
        "effective_date": anchor["effective_date"],
        "authority_url": anchor["authority_url"],
    }


def _artifact_indexes(
    inventory: dict[str, Any], manifest: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    artifacts = {row["artifact_id"]: row for row in inventory["artifacts"]}
    observations = {row["artifact_id"]: row for row in manifest["packet_observations"]}
    return artifacts, observations


def _evidence_row(
    *,
    row_number: int,
    judgment: dict[str, Any],
    requirement_ref: dict[str, Any],
    expectation: dict[str, Any],
    artifact: dict[str, Any],
    observation: dict[str, Any],
    session_contents: dict[str, str],
) -> dict[str, Any]:
    artifact_id = judgment["artifact_id"]
    failure = judgment["failure_state"]
    check_state = judgment["coverage_check_state"]
    source_text = session_contents.get(artifact_id)
    if check_state == "performed" and source_text is None:
        _fail(
            f"draft judgment {artifact_id}",
            "performed coverage requires explicit session-held content",
        )
    if failure in {"source_missing", "access_failed", "retrieval_failed"} and source_text is not None:
        _fail(
            f"draft judgment {artifact_id}.failure_state",
            "contradicts explicitly supplied session content",
        )
    expectation_pointer = judgment["expectation_pointer"]
    template = {
        "schema_version": ADVISORY_SCHEMA_VERSION,
        "surface": ADVISORY_SURFACE,
        "row_id": f"EVR-CC-{row_number:06d}",
        "coverage_subject": {
            "requirement_id": requirement_ref["requirement_id"],
            "requirement_pointer": requirement_ref["requirement_pointer"],
            "authority_anchor_pointer": requirement_ref["authority_anchor_pointer"],
            "expectation_field_id": expectation["field_id"],
            "expectation_pointer": expectation_pointer,
            "expectation_digest": digest(expectation),
            "document_locator": {
                **judgment["document_locator"],
                "provenance": DOCUMENT_LOCATOR_PROVENANCE,
            },
        },
        "source": {
            "artifact_id": artifact_id,
            "relative_path": artifact["relative_path"],
            "source_artifact_sha256": observation["observed_sha256"],
            "source_artifact_size_bytes": observation["observed_size_bytes"],
        },
        "anchor": {
            "kind": (
                "quote"
                if judgment["advisory_coverage_status"] in {"DOCUMENTED", "CONFLICTING"}
                else "none"
            ),
            "value_encoded": judgment["quoted_anchor_encoded"],
        },
        "content_handling": {
            "sharing_scope": "session_only",
            "rights_basis": "not_assessed",
        },
    }
    try:
        return build_advisory(
            template,
            source_text if check_state == "performed" else None,
            failure_state=failure,
            captured_at=judgment["captured_at"],
        )
    except EvidenceRowError as exc:
        _fail(f"evidence row {row_number}", str(exc))


def _finding_from_judgments(
    *,
    requirement_ref: dict[str, Any],
    expectation: dict[str, Any],
    expectation_pointer: str,
    judgments: list[dict[str, Any]],
    allowed_artifacts: set[str],
    artifacts: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    session_contents: dict[str, str],
    row_counter: list[int],
) -> dict[str, Any]:
    if not judgments:
        _fail(expectation_pointer, "is missing explicit draft accounting")
    if len(judgments) > 512:
        _fail(expectation_pointer, "exceeds 512 evidence rows")
    states = {row["coverage_check_state"] for row in judgments}
    statuses = {row["advisory_coverage_status"] for row in judgments}
    if len(states) != 1 or len(statuses) != 1:
        _fail(expectation_pointer, "cannot mix check states or advisory statuses")
    check_state = next(iter(states))
    status = next(iter(statuses))
    if status == "CONFLICTING":
        if len(judgments) < 2:
            _fail(expectation_pointer, "CONFLICTING requires two distinct positive passages")
    elif status == "NOT_LOCATED":
        if {row["artifact_id"] for row in judgments} != allowed_artifacts or len(judgments) != len(allowed_artifacts):
            _fail(
                expectation_pointer,
                "NOT_LOCATED must account exactly once for every eligible artifact",
            )
    elif len(judgments) != 1:
        _fail(expectation_pointer, "DOCUMENTED and not_checked findings require one evidence row")

    evidence: list[dict[str, Any]] = []
    for judgment in sorted(
        judgments,
        key=lambda row: (
            row["artifact_id"],
            row["document_locator"]["kind"],
            row["document_locator"]["value"],
            row["quoted_anchor_encoded"],
            "" if row["captured_at"] is None else row["captured_at"],
            "" if row["failure_state"] is None else row["failure_state"],
            "" if row["advisory_coverage_status"] is None else row["advisory_coverage_status"],
        ),
    ):
        artifact_id = judgment["artifact_id"]
        if artifact_id not in allowed_artifacts:
            _fail(
                expectation_pointer,
                f"artifact {artifact_id!r} is not in a packet-owned DOCUMENTED entry",
            )
        artifact = artifacts.get(artifact_id)
        observation = observations.get(artifact_id)
        if artifact is None or observation is None or observation["state"] != "located":
            _fail(expectation_pointer, f"artifact {artifact_id!r} lacks a located observation")
        row_counter[0] += 1
        evidence.append(
            _evidence_row(
                row_number=row_counter[0],
                judgment=judgment,
                requirement_ref=requirement_ref,
                expectation=expectation,
                artifact=artifact,
                observation=observation,
                session_contents=session_contents,
            )
        )
    if status == "CONFLICTING":
        replay_row_identities = {
            (
                row["source"]["artifact_id"],
                row["excerpt"]["excerpt_sha256"],
                row["excerpt"]["source_span_utf8"]["start"],
                row["excerpt"]["source_span_utf8"]["end"],
                row["coverage_subject"]["document_locator"]["kind"],
                row["coverage_subject"]["document_locator"]["value"],
            )
            for row in evidence
        }
        replay_passage_identities = {
            identity[:4] for identity in replay_row_identities
        }
        if len(replay_row_identities) < 2 or len(replay_passage_identities) < 2:
            _fail(
                expectation_pointer,
                "CONFLICTING requires two distinct replayed passage hashes or UTF-8 spans",
            )
    reason = (
        STATUS_REASON[status]
        if check_state == "performed"
        else FAILURE_REASON[judgments[0]["failure_state"]]
    )
    return {
        "requirement_id": requirement_ref["requirement_id"],
        "authority_anchor_pointer": requirement_ref["authority_anchor_pointer"],
        "expectation_ref": {
            "field_id": expectation["field_id"],
            "expectation_pointer": expectation_pointer,
            "expectation_digest": digest(expectation),
        },
        "coverage_check_state": check_state,
        "advisory_coverage_status": status,
        "reason_codes": [reason],
        "evidence_rows": evidence,
    }


def _ineligible_result(
    requirement_ref: dict[str, Any],
    requirement: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    applicability_unresolved: bool = False,
) -> dict[str, Any] | None:
    external = [row for row in entries if row["responsibility"] == "external_dependency"]
    waiver = [
        row
        for row in entries
        if row["responsibility"] == "packet_owned"
        if row["status"] == "ACCEPTANCE_UNVERIFIED"
        and "WAIVER_OR_EXCEPTION_CLAIM_UNVERIFIED" in row["reason_codes"]
    ]
    conflicts = [
        row
        for row in entries
        if row["responsibility"] == "packet_owned" and row["status"] == "CONFLICTING"
    ]
    gaps = [
        row
        for row in entries
        if row["responsibility"] == "packet_owned" and row["status"] == "NOT_LOCATED"
    ]
    documented = [
        row
        for row in entries
        if row["responsibility"] == "packet_owned" and row["status"] == "DOCUMENTED"
    ]
    status: str | None = None
    reasons: list[str]
    if applicability_unresolved:
        status = "APPLICABILITY_UNRESOLVED"
        reasons = ["APPLICABILITY_UNRESOLVED"]
    elif conflicts:
        reasons = ["DETERMINISTIC_PACKET_CONFLICT"]
    elif gaps:
        reasons = ["DETERMINISTIC_PACKET_GAP"]
    elif waiver:
        status = "ACCEPTANCE_UNVERIFIED"
        reasons = ["WAIVER_OR_EXCEPTION_BOUNDARY", "INSTITUTIONAL_ACCEPTANCE_REQUIRED"]
    elif documented and not requirement["structured_expectations"]:
        reasons = ["NO_PROFILED_STRUCTURED_EXPECTATIONS"]
    elif documented:
        # External dependencies remain visible in deterministic_entry_refs but
        # do not suppress passage checks over packet-owned documented artifacts.
        return None
    elif external:
        status = "ACCEPTANCE_UNVERIFIED"
        reasons = ["EXTERNAL_DEPENDENCY", "INSTITUTIONAL_ACCEPTANCE_REQUIRED"]
    else:
        reasons = ["DETERMINISTIC_PACKET_GAP"]
    return {
        "requirement_ref": copy.deepcopy(requirement_ref),
        "authority_anchor_ref": _authority_anchor_ref(
            requirement, requirement_ref["requirement_pointer"]
        ),
        "deterministic_entry_refs": [_manifest_entry_ref(row) for row in entries],
        "coverage_check_state": "not_checked",
        "advisory_coverage_status": status,
        "reason_codes": reasons,
        "expectation_findings": [],
    }


def _overlay_applicability_unresolved(manifest: dict[str, Any]) -> bool:
    """Return the sole open-gate unresolved state supported by #681.

    Exact #667 replay guarantees that closed authority/capability states never
    carry requirement entries.  Missing overlay selection is different: base
    entries remain available, but their applicability is not complete enough
    for passage evaluation.
    """

    reasons = manifest["unresolved_reasons"]
    if not reasons:
        return False
    if all(row["code"] == "OVERLAY_SELECTION_NOT_PROVIDED" for row in reasons):
        return True
    _fail(
        "manifest.unresolved_reasons",
        "an open #681 gate permits only unresolved overlay-selection accounting",
    )


def _preflight(
    manifest: dict[str, Any],
    inventory: dict[str, Any],
    packet_root: Path | str,
    context: dict[str, Any],
    registry: dict[str, Any],
    resolved: dict[str, Any],
) -> dict[str, Any]:
    """Replay the deterministic layer and fail before advisory inputs are read."""

    try:
        validate_submission_packet_manifest(
            manifest,
            inventory,
            packet_root,
            context=context,
            registry=registry,
            resolved=resolved,
        )
    except (ContractError, OSError, ValueError, RecursionError, UnicodeError) as exc:
        _fail("manifest replay", str(exc))
    binding = manifest["authority_binding"]
    if (
        binding["state"] != "replay_validated"
        or binding["resolution_state"] != "resolved"
        or not binding["downstream_gate"]["profile_dependent_result_allowed"]
    ):
        _fail(
            "manifest.authority_binding",
            "#681 requires a replay-validated resolved authority context with an open downstream gate",
        )
    if manifest["capability_envelope"]["state"] != "within_v1":
        _fail(
            "manifest.capability_envelope",
            "#681 requires the replay-validated packet to be within the #667 V1 envelope",
        )
    return binding


def finalize_advisory(
    draft: dict[str, Any],
    inventory: dict[str, Any],
    packet_root: Path | str,
    context: dict[str, Any],
    registry: dict[str, Any],
    resolved: dict[str, Any],
    manifest: dict[str, Any],
    session_sources: Mapping[str, str],
) -> dict[str, Any]:
    """Finalize explicit evaluator judgments after exact #667 replay."""

    binding = _preflight(
        manifest, inventory, packet_root, context, registry, resolved
    )
    judgments = _validate_draft(draft)
    applicability_unresolved = _overlay_applicability_unresolved(manifest)
    # Do not inspect supplied content when authority applicability is unresolved.
    # Draft observations are still parsed so any attempt to target such a
    # requirement fails as an explicit ineligible judgment below.
    contents = (
        {}
        if applicability_unresolved
        else _validate_session_contents(session_sources)
    )
    artifacts, observations = _artifact_indexes(inventory, manifest)
    unknown_sources = set(contents) - set(artifacts)
    if unknown_sources:
        _fail("session_contents", f"unknown artifact id(s): {', '.join(sorted(unknown_sources))}")

    entries_by_requirement: dict[str, list[dict[str, Any]]] = {}
    requirement_refs: dict[str, dict[str, Any]] = {}
    for entry in manifest["entries"]:
        requirement_id = entry["requirement_ref"]["requirement_id"]
        previous = requirement_refs.setdefault(requirement_id, entry["requirement_ref"])
        if previous != entry["requirement_ref"]:
            _fail("manifest.entries", f"inconsistent requirement_ref for {requirement_id}")
        entries_by_requirement.setdefault(requirement_id, []).append(entry)

    judgments_by_expectation: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for judgment in judgments:
        judgments_by_expectation.setdefault(
            (judgment["requirement_id"], judgment["expectation_pointer"]), []
        ).append(judgment)

    results: list[dict[str, Any]] = []
    consumed_judgments: set[tuple[str, str]] = set()
    row_counter = [0]
    for requirement_id, entries in entries_by_requirement.items():
        requirement_ref = requirement_refs[requirement_id]
        requirement = _pointer_get(
            registry,
            requirement_ref["requirement_pointer"],
            f"manifest requirement {requirement_id}",
        )
        if not isinstance(requirement, dict) or requirement.get("requirement_id") != requirement_id:
            _fail("manifest.entries", f"requirement pointer mismatch for {requirement_id}")
        if digest(requirement) != requirement_ref["requirement_digest"]:
            _fail("manifest.entries", f"requirement digest mismatch for {requirement_id}")
        ineligible = _ineligible_result(
            requirement_ref,
            requirement,
            entries,
            applicability_unresolved=applicability_unresolved,
        )
        if ineligible is not None:
            results.append(ineligible)
            continue

        allowed_artifacts = {
            artifact_id
            for entry in entries
            if entry["responsibility"] == "packet_owned" and entry["status"] == "DOCUMENTED"
            for artifact_id in entry["matched_artifact_ids"]
        }
        findings: list[dict[str, Any]] = []
        for index, expectation in enumerate(requirement["structured_expectations"]):
            pointer = requirement_ref["requirement_pointer"] + f"/structured_expectations/{index}"
            key = (requirement_id, pointer)
            finding = _finding_from_judgments(
                requirement_ref=requirement_ref,
                expectation=expectation,
                expectation_pointer=pointer,
                judgments=judgments_by_expectation.get(key, []),
                allowed_artifacts=allowed_artifacts,
                artifacts=artifacts,
                observations=observations,
                session_contents=contents,
                row_counter=row_counter,
            )
            consumed_judgments.add(key)
            findings.append(finding)

        if any(row["coverage_check_state"] == "not_checked" for row in findings):
            check_state = "not_checked"
            status = None
            reasons = sorted(
                {
                    reason
                    for row in findings
                    if row["coverage_check_state"] == "not_checked"
                    for reason in row["reason_codes"]
                }
            )
        else:
            check_state = "performed"
            finding_statuses = [row["advisory_coverage_status"] for row in findings]
            if "CONFLICTING" in finding_statuses:
                status = "CONFLICTING"
            elif "NOT_LOCATED" in finding_statuses:
                status = "NOT_LOCATED"
            else:
                status = "DOCUMENTED"
            reasons = [STATUS_REASON[status]]
        results.append(
            {
                "requirement_ref": copy.deepcopy(requirement_ref),
                "authority_anchor_ref": _authority_anchor_ref(
                    requirement, requirement_ref["requirement_pointer"]
                ),
                "deterministic_entry_refs": [_manifest_entry_ref(row) for row in entries],
                "coverage_check_state": check_state,
                "advisory_coverage_status": status,
                "reason_codes": reasons,
                "expectation_findings": findings,
            }
        )

    extra = set(judgments_by_expectation) - consumed_judgments
    if extra:
        formatted = ", ".join(f"{req}:{pointer}" for req, pointer in sorted(extra))
        _fail("draft.judgments", f"targets ineligible or unknown expectations: {formatted}")

    context_pointer = binding["context_pointer"]
    registry_pointer = binding["registry_pointer"]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "layer": LAYER,
        "evaluation_status": EVALUATION_STATUS,
        "input_binding": {
            "manifest_schema_version": manifest["schema_version"],
            "manifest_digest": manifest["manifest_digest"],
            "inventory_id": manifest["inventory_pointer"]["inventory_id"],
            "inventory_digest": manifest["inventory_pointer"]["inventory_digest"],
            "observation_digest": manifest["packet_pointer"]["observation_digest"],
            "context_record_id": context_pointer["context_record_id"],
            "context_digest": context_pointer["context_digest"],
            "registry_id": registry_pointer["registry_id"],
            "registry_version": registry_pointer["registry_version"],
            "registry_as_of": registry_pointer["as_of"],
            "registry_digest": registry_pointer["registry_digest"],
            "resolved_digest": binding["resolved_digest"],
        },
        "deterministic_status": {
            "review_pathway": manifest["administrative_status"]["review_pathway"],
            "submission_readiness": manifest["administrative_status"]["submission_readiness"],
            "authorization_status": copy.deepcopy(
                manifest["administrative_status"]["authorization_status"]
            ),
            "review_timeline": manifest["administrative_status"]["review_timeline"],
            "acceptance_status": manifest["acceptance_boundary"]["status"],
        },
        "requirement_results": results,
        "excluded_requirements": copy.deepcopy(manifest["excluded_requirements"]),
        "boundary": {
            "deterministic_status_unchanged": True,
            "submission_readiness_unchanged": True,
            "authorization_status_unchanged": True,
            "institutional_acceptance_unchanged": True,
            "adequacy_not_assessed": True,
        },
    }
    report["report_digest"] = digest(report)
    _enforce_advisory_byte_limit(report)
    return report


def validate_advisory(
    advisory: dict[str, Any],
    draft: dict[str, Any],
    inventory: dict[str, Any],
    packet_root: Path | str,
    context: dict[str, Any],
    registry: dict[str, Any],
    resolved: dict[str, Any],
    manifest: dict[str, Any],
    session_sources: Mapping[str, str],
) -> None:
    """Require canonical exact replay from every named input."""

    _preflight(manifest, inventory, packet_root, context, registry, resolved)
    _enforce_advisory_byte_limit(advisory)
    expected = finalize_advisory(
        draft,
        inventory,
        packet_root,
        context,
        registry,
        resolved,
        manifest,
        session_sources,
    )
    if _canonical_bytes(advisory) != _canonical_bytes(expected):
        _fail("report", "does not exactly match deterministic replay from named inputs")


def _md(value: Any) -> str:
    if value is None:
        return "not checked"
    return "".join(
        f"&#{ord(character)};"
        if (
            character.isascii()
            and not character.isalnum()
            and not character.isspace()
        )
        or unicodedata.category(character) in {"Cc", "Cf", "Zl", "Zp"}
        else character
        for character in str(value)
    )


def render_advisory(
    advisory: dict[str, Any],
    draft: dict[str, Any],
    inventory: dict[str, Any],
    packet_root: Path | str,
    context: dict[str, Any],
    registry: dict[str, Any],
    resolved: dict[str, Any],
    manifest: dict[str, Any],
    session_sources: Mapping[str, str],
    *,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """Replay and render the final advisory plus replay-bound evidence pages."""

    validate_advisory(
        advisory,
        draft,
        inventory,
        packet_root,
        context,
        registry,
        resolved,
        manifest,
        session_sources,
    )
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        _fail("page", "must be a positive integer")
    if (
        isinstance(page_size, bool)
        or not isinstance(page_size, int)
        or page_size < 1
        or page_size > MAX_RENDER_PAGE_SIZE
    ):
        _fail("page_size", f"must be an integer from 1 through {MAX_RENDER_PAGE_SIZE}")
    deterministic = advisory["deterministic_status"]
    authorization = deterministic["authorization_status"]
    lines = [
        "# LLM-ADVISORY Content-Coverage Advisory",
        "",
        "Evaluation status: UNMEASURED",
        "",
        "This advisory records bounded passage observations only. It does not assess adequacy or alter deterministic packet status, submission readiness, authorization, or institutional acceptance.",
        "",
        "## Deterministic Status — Copied Unchanged",
        "",
        f"Review pathway: {deterministic['review_pathway']}",
        f"Submission readiness: {deterministic['submission_readiness']}",
        f"Authorization status: {authorization['value']}",
        f"Review timeline: {deterministic['review_timeline']}",
        f"Authorization source reference: {_md(authorization['source_reference'])}",
        f"Authorization provenance: {_md(authorization['provenance'])}",
        f"Institutional acceptance: {deterministic['acceptance_status']}",
        "",
        "## Requirement Results",
        "",
        "| Requirement | Authority source | Provision | Effective date | Anchor pointer | Anchor digest | Authority URL | Check state | LLM-ADVISORY coverage status | Reasons | Expectations |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    if advisory["requirement_results"]:
        for result in advisory["requirement_results"]:
            lines.append(
                "| "
                + " | ".join(
                    _md(value)
                    for value in (
                        result["requirement_ref"]["requirement_id"],
                        result["authority_anchor_ref"]["source_id"],
                        result["authority_anchor_ref"]["provision"],
                        result["authority_anchor_ref"]["effective_date"],
                        result["authority_anchor_ref"]["authority_anchor_pointer"],
                        result["authority_anchor_ref"]["authority_anchor_digest"],
                        result["authority_anchor_ref"]["authority_url"],
                        result["coverage_check_state"],
                        result["advisory_coverage_status"],
                        ", ".join(result["reason_codes"]),
                        len(result["expectation_findings"]),
                    )
                )
                + " |"
            )
    else:
        lines.append(
            "| none | none | none | none | none | none | none | none | none | "
            "no applicable advisory requirement results | 0 |"
        )

    lines.extend(
        [
            "",
            "## Excluded Requirements",
            "",
            "| Requirement | Requirement pointer | Applicability | Exclusion basis |",
            "|---|---|---|---|",
        ]
    )
    if advisory["excluded_requirements"]:
        for excluded in advisory["excluded_requirements"]:
            lines.append(
                "| "
                + " | ".join(
                    _md(value)
                    for value in (
                        excluded["requirement_ref"]["requirement_id"],
                        excluded["requirement_ref"]["requirement_pointer"],
                        excluded["requirement_ref"]["applicability"],
                        excluded["exclusion_basis"],
                    )
                )
                + " |"
            )
    else:
        lines.append("| none | none | none | none |")

    all_rows = [
        row
        for result in advisory["requirement_results"]
        for finding in result["expectation_findings"]
        for row in finding["evidence_rows"]
    ]
    if all_rows:
        lines.extend(["", "## Bounded Evidence Rows", ""])
        lines.append(
            render_evidence_rows_markdown(
                all_rows,
                page=page,
                page_size=page_size,
                session_sources=session_sources,
            ).rstrip("\n")
        )
        lines.append("")
    elif page != 1:
        _fail("page", "cannot exceed page 1 when no evidence rows exist")
    lines.extend(
        [
            "> **Human-subjects boundary:** This output does not authorize recruitment, consent, access to identifiable data, intervention, or data collection.",
            "",
        ]
    )
    return "\n".join(lines)


def _session_map(path: Path) -> dict[str, str]:
    try:
        value = load_json(path)
    except (ContractError, OSError, ValueError, RecursionError, UnicodeError) as exc:
        raise ContentCoverageAdvisoryInputError(str(exc)) from exc
    try:
        return _validate_session_contents(value)
    except ContentCoverageAdvisoryError as exc:
        raise ContentCoverageAdvisoryInputError(str(exc)) from exc


def _emit(text: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(text)
    else:
        output.write_text(text, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "validate", "render"):
        command = subparsers.add_parser(name, allow_abbrev=False)
        command.add_argument("--draft", type=Path, required=True)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--inventory", type=Path, required=True)
        command.add_argument("--packet-root", type=Path, required=True)
        command.add_argument("--context", type=Path, required=True)
        command.add_argument("--registry", type=Path, required=True)
        command.add_argument("--resolved", type=Path, required=True)
        command.add_argument("--source-map", type=Path, required=True)
        if name in {"validate", "render"}:
            command.add_argument("--advisory", type=Path, required=True)
        if name in {"build", "render"}:
            command.add_argument("--output", type=Path)
        if name == "render":
            command.add_argument("--page", type=int, default=1)
            command.add_argument("--page-size", type=int, default=25)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = load_json(args.manifest)
        inventory = load_json(args.inventory)
        context = load_json(args.context)
        registry = load_json(args.registry)
        resolved = load_json(args.resolved)
        # The deterministic replay/gates precede even opening advisory draft or
        # session-content paths.  A closed gate cannot be turned into an input
        # read oracle by naming an unavailable --source-map.
        _preflight(
            manifest,
            inventory,
            args.packet_root,
            context,
            registry,
            resolved,
        )
        draft = load_json(args.draft)
        # Overlay selection may remain explicitly unprovided while the base
        # authority gate is open.  In that state #681 reports applicability as
        # unresolved and must not even open the named content map.
        session_sources = (
            {}
            if _overlay_applicability_unresolved(manifest)
            else _session_map(args.source_map)
        )
        if args.command == "build":
            advisory = finalize_advisory(
                draft,
                inventory,
                args.packet_root,
                context,
                registry,
                resolved,
                manifest,
                session_sources,
            )
            # Do not append a transport newline: an exactly 8 MiB canonical
            # carrier must remain loadable through the shared 8 MiB JSON cap.
            _emit(_canonical_bytes(advisory).decode("utf-8"), args.output)
            return 0
        advisory = load_json(args.advisory)
        validate_advisory(
            advisory,
            draft,
            inventory,
            args.packet_root,
            context,
            registry,
            resolved,
            manifest,
            session_sources,
        )
        if args.command == "validate":
            print("Content-coverage advisory validation passed (#681).")
            return 0
        _emit(
            render_advisory(
                advisory,
                draft,
                inventory,
                args.packet_root,
                context,
                registry,
                resolved,
                manifest,
                session_sources,
                page=args.page,
                page_size=args.page_size,
            ),
            args.output,
        )
        return 0
    except ContentCoverageAdvisoryInputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (
        ContentCoverageAdvisoryError,
        ContractError,
        EvidenceRowError,
        OSError,
        ValueError,
        RecursionError,
        UnicodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


__all__ = [
    "ContentCoverageAdvisoryError",
    "ContentCoverageAdvisoryInputError",
    "DRAFT_SCHEMA_VERSION",
    "EVALUATION_STATUS",
    "LAYER",
    "REPORT_SCHEMA_VERSION",
    "finalize_advisory",
    "main",
    "render_advisory",
    "validate_advisory",
]


if __name__ == "__main__":
    raise SystemExit(main())
