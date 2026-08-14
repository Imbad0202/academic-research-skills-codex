#!/usr/bin/env python3
"""Build a deterministic, pointer-only human-subjects packet manifest.

This checker observes only explicitly inventoried regular files.  It does not
scan a packet, interpret document prose, choose an authority, determine a
review pathway, verify institutional acceptance, or grant authorization.
"""
from __future__ import annotations

import argparse
import copy
import errno
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

try:  # Direct script execution puts scripts/ on sys.path.
    from resolve_human_subjects_authority import (
        ContractError,
        load_json,
        validate_resolved_context,
    )
except ModuleNotFoundError:  # Package-style imports used by some test runners.
    from scripts.resolve_human_subjects_authority import (  # type: ignore[no-redef]
        ContractError,
        load_json,
        validate_resolved_context,
    )


INVENTORY_SCHEMA_VERSION = "submission-packet-inventory/1.0"
MANIFEST_SCHEMA_VERSION = "submission-packet-manifest/1.0"
BOUNDARY_FOOTER = (
    "Human-subjects boundary: This output does not authorize recruitment, "
    "consent, access to identifiable data, intervention, or data collection."
)
REVIEW_PATHWAY = "institutional determination required"
REVIEW_TIMELINE = "unknown — obtain current institutional estimate"
ACCEPTANCE_REASON = "INSTITUTIONAL_DETERMINATION_REQUIRED"

STATUSES = {
    "DOCUMENTED",
    "NOT_LOCATED",
    "CONFLICTING",
    "APPLICABILITY_UNRESOLVED",
    "ACCEPTANCE_UNVERIFIED",
}
READINESS_VALUES = {"gaps_located", "no_listed_gaps_located", "unresolved"}
AUTHORIZATION_VALUES = {"documented", "not_provided", "cannot_verify"}
GLOBAL_REASON_CODES = {
    "AUTHORITY_INPUT_NOT_PROVIDED",
    "AUTHORITY_RESOLUTION_NOT_PERMITTED",
    "V1_ENVELOPE_FACT_MISSING",
    "V1_ENVELOPE_FACT_UNKNOWN",
    "V1_ENVELOPE_OUTSIDE",
    "OVERLAY_SELECTION_NOT_PROVIDED",
}
ENTRY_REASON_ORDER = (
    "STRUCTURE_DOCUMENTED",
    "EXTERNAL_HOLDER_DEPENDENCY",
    "WAIVER_OR_EXCEPTION_CLAIM_UNVERIFIED",
    "EXPECTED_PACKET_ARTIFACT_NOT_LOCATED",
    "DUPLICATE_EVIDENCE_BINDING",
    "DECLARED_ATTACHMENT_NOT_LOCATED",
    "ARTIFACT_DIGEST_MISMATCH",
    "ARTIFACT_SIZE_MISMATCH",
    "ARTIFACT_TYPE_MISMATCH",
    "ARTIFACT_HOLDER_MISMATCH",
    "CERTIFICATE_HOLDER_MISMATCH",
    "DECLARED_STRUCTURE_CONFLICT",
)
ENTRY_REASON_CODES = set(ENTRY_REASON_ORDER)
OBSERVATION_REASON_CODES = {
    "STRUCTURE_DOCUMENTED",
    "DECLARED_ATTACHMENT_NOT_LOCATED",
    "ARTIFACT_DIGEST_MISMATCH",
    "ARTIFACT_SIZE_MISMATCH",
    "CERTIFICATE_HOLDER_MISMATCH",
    "DECLARED_STRUCTURE_CONFLICT",
}
ENVELOPE_FACTS: tuple[tuple[str, bool], ...] = (
    ("packet_v1.non_clinical", True),
    ("packet_v1.single_institution", True),
    ("packet_v1.competent_adults_only", True),
    ("packet_v1.biospecimens_involved", False),
    ("packet_v1.regulated_clinical_trial", False),
    ("packet_v1.cross_border_material_transfer", False),
    ("packet_v1.multisite_reliance", False),
)

ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
MEDIA_TYPE_RE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$")
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_ITEMS = 512
MAX_MANIFEST_ENTRIES = 4096
MAX_EXCLUDED_REQUIREMENTS = 4096
MAX_CONSUMER_SCOPES = 512
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
DESCRIPTOR_RELATIVE_OPEN_SUPPORTED = (
    os.name == "posix"
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
    and os.open in os.supports_dir_fd
)


def _fail(path: str, message: str) -> NoReturn:
    raise ContractError(f"{path}: {message}")


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


def _array(
    value: Any,
    path: str,
    *,
    maximum: int = MAX_ITEMS,
    minimum: int = 0,
) -> list[Any]:
    if not isinstance(value, list):
        _fail(path, "must be an array")
    if len(value) < minimum:
        _fail(path, f"must contain at least {minimum} item(s)")
    if len(value) > maximum:
        _fail(path, f"exceeds {maximum} items")
    return value


def _text(value: Any, path: str, *, maximum: int = 1024) -> str:
    if not isinstance(value, str) or not value:
        _fail(path, "must be a non-empty string")
    if len(value) > maximum:
        _fail(path, f"must not exceed {maximum} characters")
    if any(
        unicodedata.category(ch) in {"Cc", "Cf", "Cs"}
        or "\U00013430" <= ch <= "\U0001345f"
        for ch in value
    ):
        _fail(path, "must not contain control, format, or surrogate characters")
    return value


def _identifier(value: Any, path: str) -> str:
    text = _text(value, path, maximum=200)
    if ID_RE.fullmatch(text) is None:
        _fail(path, "must use lowercase letters, digits, dot, underscore, or hyphen")
    return text


def _version(value: Any, path: str) -> str:
    text = _text(value, path, maximum=200)
    if VERSION_RE.fullmatch(text) is None:
        _fail(path, "has an invalid version token")
    return text


def _sha(value: Any, path: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    text = _text(value, path, maximum=64)
    if SHA_RE.fullmatch(text) is None:
        _fail(path, "must be 64 lowercase hexadecimal characters")
    return text


def _iso_date(value: Any, path: str, *, nullable: bool = False) -> date | None:
    if nullable and value is None:
        return None
    text = _text(value, path, maximum=10)
    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text) is None:
            raise ValueError
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ContractError(f"{path}: must be a real ISO 8601 date") from exc


def _unique_identifiers(
    value: Any,
    path: str,
    *,
    maximum: int = MAX_ITEMS,
    minimum: int = 0,
) -> list[str]:
    rows = _array(value, path, maximum=maximum, minimum=minimum)
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(rows):
        item_id = _identifier(item, f"{path}[{index}]")
        if item_id in seen:
            _fail(path, f"duplicate identifier: {item_id}")
        seen.add(item_id)
        result.append(item_id)
    return result


def _relative_path(value: Any, path: str) -> str:
    text = _text(value, path, maximum=1024)
    if "\\" in text:
        _fail(path, "must use POSIX separators")
    if text in {".", ".."}:
        _fail(path, "must name a file below the packet root")
    if re.match(r"^[A-Za-z]:", text):
        _fail(path, "must not use a drive-qualified path")
    pure = PurePosixPath(text)
    if pure.is_absolute():
        _fail(path, "must be packet-relative")
    if text.startswith("/") or text.endswith("/") or "//" in text:
        _fail(path, "must be a canonical POSIX relative path")
    if any(part in {"", ".", ".."} for part in pure.parts):
        _fail(path, "must not contain empty, dot, or dot-dot components")
    if pure.as_posix() != text:
        _fail(path, "must be a normalized POSIX relative path")
    return text


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContractError(f"value is not canonical JSON: {exc}") from exc


def _enforce_manifest_byte_limit(manifest: dict[str, Any]) -> None:
    manifest_size = len(_canonical_bytes(manifest))
    if manifest_size > MAX_MANIFEST_BYTES:
        _fail(
            "manifest",
            f"canonical JSON exceeds the {MAX_MANIFEST_BYTES}-byte V1 limit",
        )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _semantic_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Normalize arrays whose inventory meaning is explicitly order-insensitive."""
    normalized = copy.deepcopy(inventory)
    normalized["packet_responsibility_role_ids"].sort()
    for claim in normalized["waiver_or_exception_claims"]:
        claim["route_requirement_ids"].sort()
    normalized["waiver_or_exception_claims"].sort(
        key=lambda row: (row["requirement_id"], row["decision_artifact_id"] or "")
    )
    for artifact in normalized["artifacts"]:
        artifact["evidence_bindings"].sort(
            key=lambda row: (row["requirement_id"], row["evidence_id"])
        )
        artifact["declared_structure"]["signature_blocks"].sort(
            key=lambda row: (row["role_id"], row["state"])
        )
    normalized["artifacts"].sort(
        key=lambda row: (row["artifact_id"], row["relative_path"])
    )
    return normalized


def validate_submission_packet_inventory(inventory: dict[str, Any]) -> None:
    """Validate the closed submission-packet inventory contract."""
    root = _closed(
        inventory,
        "inventory",
        {
            "schema_version",
            "inventory_id",
            "declared_by",
            "packet_responsibility_role_ids",
            "authorization_status_input",
            "waiver_or_exception_claims",
            "artifacts",
        },
    )
    if root["schema_version"] != INVENTORY_SCHEMA_VERSION:
        _fail("inventory.schema_version", f"must equal {INVENTORY_SCHEMA_VERSION}")
    _identifier(root["inventory_id"], "inventory.inventory_id")
    if root["declared_by"] != "author":
        _fail("inventory.declared_by", "must equal author")
    _unique_identifiers(
        root["packet_responsibility_role_ids"],
        "inventory.packet_responsibility_role_ids",
        maximum=128,
        minimum=1,
    )

    authorization = _closed(
        root["authorization_status_input"],
        "inventory.authorization_status_input",
        {"value", "source_reference", "provenance"},
    )
    if authorization["value"] not in AUTHORIZATION_VALUES:
        _fail(
            "inventory.authorization_status_input.value",
            "must be documented, not_provided, or cannot_verify",
        )
    if authorization["provenance"] != "caller_supplied_no_derivation":
        _fail(
            "inventory.authorization_status_input.provenance",
            "must equal caller_supplied_no_derivation",
        )
    if authorization["value"] == "documented":
        _identifier(
            authorization["source_reference"],
            "inventory.authorization_status_input.source_reference",
        )
    elif authorization["source_reference"] is not None:
        _fail(
            "inventory.authorization_status_input.source_reference",
            "must be null unless value is documented",
        )

    claim_requirement_ids: set[str] = set()
    for index, raw_claim in enumerate(
        _array(root["waiver_or_exception_claims"], "inventory.waiver_or_exception_claims")
    ):
        path = f"inventory.waiver_or_exception_claims[{index}]"
        claim = _closed(
            raw_claim,
            path,
            {"requirement_id", "route_requirement_ids", "decision_artifact_id", "declared_by"},
        )
        requirement_id = _identifier(claim["requirement_id"], f"{path}.requirement_id")
        if requirement_id in claim_requirement_ids:
            _fail(f"{path}.requirement_id", "duplicates another waiver or exception claim")
        claim_requirement_ids.add(requirement_id)
        _unique_identifiers(
            claim["route_requirement_ids"], f"{path}.route_requirement_ids", maximum=128
        )
        if claim["decision_artifact_id"] is not None:
            _identifier(claim["decision_artifact_id"], f"{path}.decision_artifact_id")
        if claim["declared_by"] != "author":
            _fail(f"{path}.declared_by", "must equal author")

    artifact_ids: set[str] = set()
    relative_paths: set[str] = set()
    artifacts = _array(root["artifacts"], "inventory.artifacts")
    for index, raw_artifact in enumerate(artifacts):
        path = f"inventory.artifacts[{index}]"
        artifact = _closed(
            raw_artifact,
            path,
            {
                "artifact_id",
                "relative_path",
                "declared_sha256",
                "declared_size_bytes",
                "media_type",
                "artifact_type",
                "declared_holder_role_id",
                "evidence_bindings",
                "declared_structure",
            },
        )
        artifact_id = _identifier(artifact["artifact_id"], f"{path}.artifact_id")
        if artifact_id in artifact_ids:
            _fail(f"{path}.artifact_id", "duplicates another artifact")
        artifact_ids.add(artifact_id)
        relative_path = _relative_path(artifact["relative_path"], f"{path}.relative_path")
        if relative_path in relative_paths:
            _fail(f"{path}.relative_path", "duplicates another artifact path")
        relative_paths.add(relative_path)
        _sha(artifact["declared_sha256"], f"{path}.declared_sha256")
        size = artifact["declared_size_bytes"]
        if isinstance(size, bool) or not isinstance(size, int) or not 0 <= size <= MAX_ARTIFACT_BYTES:
            _fail(
                f"{path}.declared_size_bytes",
                f"must be an integer from 0 through {MAX_ARTIFACT_BYTES}",
            )
        media_type = _text(artifact["media_type"], f"{path}.media_type", maximum=200)
        if MEDIA_TYPE_RE.fullmatch(media_type) is None:
            _fail(f"{path}.media_type", "must be a syntactically valid media type")
        _identifier(artifact["artifact_type"], f"{path}.artifact_type")
        _identifier(artifact["declared_holder_role_id"], f"{path}.declared_holder_role_id")

        seen_bindings: set[tuple[str, str]] = set()
        for binding_index, raw_binding in enumerate(
            _array(artifact["evidence_bindings"], f"{path}.evidence_bindings")
        ):
            binding_path = f"{path}.evidence_bindings[{binding_index}]"
            binding = _closed(raw_binding, binding_path, {"requirement_id", "evidence_id"})
            key = (
                _identifier(binding["requirement_id"], f"{binding_path}.requirement_id"),
                _identifier(binding["evidence_id"], f"{binding_path}.evidence_id"),
            )
            if key in seen_bindings:
                _fail(binding_path, "duplicates another binding on this artifact")
            seen_bindings.add(key)

        structure = _closed(
            artifact["declared_structure"],
            f"{path}.declared_structure",
            {"version_id", "document_date", "signature_blocks", "certificate"},
        )
        if structure["version_id"] is not None:
            _version(structure["version_id"], f"{path}.declared_structure.version_id")
        _iso_date(
            structure["document_date"],
            f"{path}.declared_structure.document_date",
            nullable=True,
        )
        signature_roles: set[str] = set()
        for signature_index, raw_signature in enumerate(
            _array(
                structure["signature_blocks"],
                f"{path}.declared_structure.signature_blocks",
                maximum=128,
            )
        ):
            signature_path = (
                f"{path}.declared_structure.signature_blocks[{signature_index}]"
            )
            signature = _closed(raw_signature, signature_path, {"role_id", "state"})
            role_id = _identifier(signature["role_id"], f"{signature_path}.role_id")
            if role_id in signature_roles:
                _fail(f"{signature_path}.role_id", "duplicates another signature role")
            signature_roles.add(role_id)
            if signature["state"] not in {"present", "not_located", "unknown"}:
                _fail(
                    f"{signature_path}.state", "must be present, not_located, or unknown"
                )
        certificate = structure["certificate"]
        if certificate is not None:
            certificate_path = f"{path}.declared_structure.certificate"
            cert = _closed(
                certificate,
                certificate_path,
                {"certificate_id", "holder_role_id", "issued_on", "expires_on"},
            )
            _identifier(cert["certificate_id"], f"{certificate_path}.certificate_id")
            _identifier(cert["holder_role_id"], f"{certificate_path}.holder_role_id")
            _iso_date(cert["issued_on"], f"{certificate_path}.issued_on")
            _iso_date(
                cert["expires_on"], f"{certificate_path}.expires_on", nullable=True
            )

    for index, claim in enumerate(root["waiver_or_exception_claims"]):
        artifact_id = claim["decision_artifact_id"]
        if artifact_id is not None and artifact_id not in artifact_ids:
            _fail(
                f"inventory.waiver_or_exception_claims[{index}].decision_artifact_id",
                "does not resolve to an inventoried artifact",
            )


def _descriptor_flags(*, directory: bool) -> int:
    """Return fail-closed POSIX flags for descriptor-relative packet access."""
    if (
        not DESCRIPTOR_RELATIVE_OPEN_SUPPORTED
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
    ):
        _fail(
            "packet_root",
            "descriptor-relative O_NOFOLLOW packet access is unavailable",
        )
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    elif hasattr(os, "O_NONBLOCK"):
        # Prevent an inventoried FIFO or device from blocking before fstat can
        # reject it. O_NONBLOCK has no effect on ordinary regular-file reads.
        flags |= os.O_NONBLOCK
    else:
        _fail("packet_root", "nonblocking safe packet access is unavailable")
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _open_directory_at(
    parent_fd: int,
    component: str,
    contract_path: str,
    *,
    missing_ok: bool,
) -> int | None:
    """Open one directory component without following it or any replacement."""
    try:
        opened = os.open(
            component,
            _descriptor_flags(directory=True),
            dir_fd=parent_fd,
        )
    except FileNotFoundError:
        if missing_ok:
            return None
        _fail(contract_path, "does not exist")
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            _fail(contract_path, "contains a symlink or non-directory component")
        raise ContractError(
            f"{contract_path}: cannot safely open directory component: {exc}"
        ) from exc
    try:
        if not stat.S_ISDIR(os.fstat(opened).st_mode):
            _fail(contract_path, "contains a non-directory component")
    except BaseException:
        os.close(opened)
        raise
    return opened


def _open_packet_root(packet_root: Path) -> int:
    """Anchor an explicit packet root by walking every component by descriptor."""
    if ".." in packet_root.parts:
        _fail("packet_root", "must not contain dot-dot traversal")
    absolute = packet_root.absolute()
    if absolute == Path(absolute.anchor):
        _fail("packet_root", "must be a bounded packet directory, not a filesystem root")
    if absolute.anchor != "/":
        _fail("packet_root", "must be an absolute POSIX packet path")
    try:
        current_fd = os.open(absolute.anchor, _descriptor_flags(directory=True))
    except OSError as exc:
        raise ContractError(f"packet_root: cannot anchor filesystem root: {exc}") from exc
    try:
        for component in absolute.parts[1:]:
            next_fd = _open_directory_at(
                current_fd,
                component,
                "packet_root",
                missing_ok=False,
            )
            assert next_fd is not None
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def _open_explicit_regular_file(root_fd: int, relative_path: str) -> int | None:
    """Open one named packet member relative to an anchored root descriptor."""
    parts = PurePosixPath(relative_path).parts
    contract_path = f"packet[{relative_path!r}]"
    try:
        current_fd = os.dup(root_fd)
    except OSError as exc:
        raise ContractError(f"{contract_path}: cannot duplicate packet root: {exc}") from exc
    try:
        for component in parts[:-1]:
            next_fd = _open_directory_at(
                current_fd,
                component,
                contract_path,
                missing_ok=True,
            )
            if next_fd is None:
                return None
            os.close(current_fd)
            current_fd = next_fd
        try:
            opened = os.open(
                parts[-1],
                _descriptor_flags(directory=False),
                dir_fd=current_fd,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                _fail(contract_path, "symlinks are not allowed")
            raise ContractError(
                f"{contract_path}: cannot safely open explicitly named file: {exc}"
            ) from exc
        try:
            item_stat = os.fstat(opened)
            if not stat.S_ISREG(item_stat.st_mode):
                _fail(contract_path, "must be a regular file")
            if item_stat.st_size > MAX_ARTIFACT_BYTES:
                _fail(
                    contract_path,
                    f"exceeds the {MAX_ARTIFACT_BYTES}-byte V1 observation limit",
                )
        except BaseException:
            os.close(opened)
            raise
        return opened
    finally:
        os.close(current_fd)


def _hash_explicit_file(file_fd: int, relative_path: str) -> tuple[str, int]:
    hasher = hashlib.sha256()
    observed_size = 0
    try:
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            observed_size += len(chunk)
            if observed_size > MAX_ARTIFACT_BYTES:
                _fail(
                    f"packet[{relative_path!r}]",
                    f"exceeds the {MAX_ARTIFACT_BYTES}-byte V1 observation limit",
                )
            hasher.update(chunk)
    except OSError as exc:
        raise ContractError(f"packet[{relative_path!r}]: cannot read regular file: {exc}") from exc
    return hasher.hexdigest(), observed_size


def _located_observation_reasons(
    artifact: dict[str, Any], observed_sha256: str, observed_size: int
) -> list[str]:
    """Compare only inventory-owned byte and internal-structure declarations."""
    reasons: list[str] = []
    if observed_sha256 != artifact["declared_sha256"]:
        reasons.append("ARTIFACT_DIGEST_MISMATCH")
    if observed_size != artifact["declared_size_bytes"]:
        reasons.append("ARTIFACT_SIZE_MISMATCH")
    certificate = artifact["declared_structure"]["certificate"]
    if (
        certificate is not None
        and certificate["expires_on"] is not None
        and certificate["expires_on"] < certificate["issued_on"]
    ):
        reasons.append("DECLARED_STRUCTURE_CONFLICT")
    if (
        certificate is not None
        and certificate["holder_role_id"] != artifact["declared_holder_role_id"]
    ):
        reasons.append("CERTIFICATE_HOLDER_MISMATCH")
    return sorted(reasons)


def observe_submission_packet(
    inventory: dict[str, Any], packet_root: Path | str
) -> list[dict[str, Any]]:
    """Observe exactly the regular files listed by a validated inventory."""
    validate_submission_packet_inventory(inventory)
    root = Path(packet_root)
    root_fd = _open_packet_root(root)
    observations: list[dict[str, Any]] = []
    total_observed_size = 0
    try:
        for artifact in inventory["artifacts"]:
            relative_path = artifact["relative_path"]
            file_fd = _open_explicit_regular_file(root_fd, relative_path)
            if file_fd is None:
                observations.append(
                    {
                        "artifact_id": artifact["artifact_id"],
                        "relative_path": relative_path,
                        "state": "not_located",
                        "observed_sha256": None,
                        "observed_size_bytes": None,
                        "status": "CONFLICTING",
                        "reason_codes": ["DECLARED_ATTACHMENT_NOT_LOCATED"],
                    }
                )
                continue
            try:
                observed_sha256, observed_size = _hash_explicit_file(
                    file_fd, relative_path
                )
            finally:
                os.close(file_fd)
            total_observed_size += observed_size
            if total_observed_size > MAX_TOTAL_BYTES:
                _fail(
                    "packet",
                    f"explicitly listed files exceed the {MAX_TOTAL_BYTES}-byte V1 total limit",
                )
            reasons = _located_observation_reasons(
                artifact, observed_sha256, observed_size
            )
            observations.append(
                {
                    "artifact_id": artifact["artifact_id"],
                    "relative_path": relative_path,
                    "state": "located",
                    "observed_sha256": observed_sha256,
                    "observed_size_bytes": observed_size,
                    "status": "CONFLICTING" if reasons else "DOCUMENTED",
                    "reason_codes": reasons or ["STRUCTURE_DOCUMENTED"],
                }
            )
    finally:
        os.close(root_fd)
    observations.sort(key=lambda row: (row["artifact_id"], row["relative_path"]))
    return observations


_REQUIREMENT_REF_FIELDS = (
    "requirement_id",
    "authority_kind",
    "authority_id",
    "authority_version",
    "authority_digest",
    "axis",
    "obligated_actor",
    "consumer_scopes",
    "applicability",
    "requirement_digest",
    "requirement_pointer",
    "authority_anchor_pointer",
)


def _requirement_ref(row: dict[str, Any]) -> dict[str, Any]:
    try:
        return {field: copy.deepcopy(row[field]) for field in _REQUIREMENT_REF_FIELDS}
    except KeyError as exc:
        _fail("resolved.requirement_results", f"missing replay-bound field: {exc.args[0]}")


def _pointer_get(root: dict[str, Any], pointer: str, contract_path: str) -> Any:
    if not isinstance(pointer, str) or re.fullmatch(
        r"/(profiles|overlays)/[0-9]+/requirements/[0-9]+", pointer
    ) is None:
        _fail(contract_path, "is not an exact requirement pointer")
    value: Any = root
    for token in pointer[1:].split("/"):
        if isinstance(value, dict):
            if token not in value:
                _fail(contract_path, "does not resolve in the replay-bound registry")
            value = value[token]
        elif isinstance(value, list):
            index = int(token)
            if index >= len(value):
                _fail(contract_path, "array index is outside the replay-bound registry")
            value = value[index]
        else:
            _fail(contract_path, "traverses a non-container registry value")
    if not isinstance(value, dict):
        _fail(contract_path, "must resolve to a requirement object")
    return value


def _capability_envelope(
    context: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    declared_by_id: dict[str, dict[str, Any]] = {}
    if context is not None:
        raw_facts = context.get("declared_facts")
        if not isinstance(raw_facts, list):
            _fail("context.declared_facts", "must be an array")
        for index, row in enumerate(raw_facts):
            if not isinstance(row, dict) or not isinstance(row.get("fact_id"), str):
                _fail(f"context.declared_facts[{index}]", "must be a validated declared fact")
            declared_by_id[row["fact_id"]] = row

    facts: list[dict[str, Any]] = []
    reasons: list[dict[str, Any]] = []
    reason_codes: list[str] = []
    for fact_id, required_value in ENVELOPE_FACTS:
        declaration = declared_by_id.get(fact_id)
        if declaration is None:
            declared_state = "missing"
            declared_value = None
            reason_code = "V1_ENVELOPE_FACT_MISSING"
        elif declaration.get("state") == "unknown":
            declared_state = "unknown"
            declared_value = None
            reason_code = "V1_ENVELOPE_FACT_UNKNOWN"
        else:
            declared_state = "declared"
            declared_value = declaration.get("value")
            if not isinstance(declared_value, bool):
                _fail(
                    f"context.declared_facts[{fact_id}]",
                    "V1 envelope facts must be replay-validated booleans",
                )
            reason_code = (
                None if declared_value == required_value else "V1_ENVELOPE_OUTSIDE"
            )
        facts.append(
            {
                "fact_id": fact_id,
                "required_value": required_value,
                "declared_state": declared_state,
                "declared_value": declared_value,
            }
        )
        if reason_code is not None:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
            reasons.append(
                {
                    "status": "APPLICABILITY_UNRESOLVED",
                    "code": reason_code,
                    "fact_id": fact_id,
                    "overlay_kind": None,
                }
            )
    return (
        {
            "state": "within_v1" if not reason_codes else "unresolved",
            "facts": facts,
            "reason_codes": reason_codes,
        },
        reasons,
    )


def _authority_binding(
    resolved: dict[str, Any] | None,
) -> dict[str, Any]:
    if resolved is None:
        return {
            "state": "not_provided",
            "context_pointer": None,
            "registry_pointer": None,
            "resolved_digest": None,
            "resolution_state": None,
            "downstream_gate": None,
        }
    _iso_date(
        resolved["registry_pointer"]["as_of"],
        "resolved.registry_pointer.as_of",
    )
    return {
        "state": "replay_validated",
        "context_pointer": copy.deepcopy(resolved["context_pointer"]),
        "registry_pointer": copy.deepcopy(resolved["registry_pointer"]),
        "resolved_digest": resolved["resolved_digest"],
        "resolution_state": resolved["resolution_state"],
        "downstream_gate": copy.deepcopy(resolved["downstream_gate"]),
    }


def _global_unresolved_reasons(
    *,
    resolved: dict[str, Any] | None,
    context: dict[str, Any] | None,
    envelope_reasons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    if resolved is None:
        reasons.append(
            {
                "status": "APPLICABILITY_UNRESOLVED",
                "code": "AUTHORITY_INPUT_NOT_PROVIDED",
                "fact_id": None,
                "overlay_kind": None,
            }
        )
    elif not resolved["downstream_gate"]["profile_dependent_result_allowed"]:
        reasons.append(
            {
                "status": "APPLICABILITY_UNRESOLVED",
                "code": "AUTHORITY_RESOLUTION_NOT_PERMITTED",
                "fact_id": None,
                "overlay_kind": None,
            }
        )
    reasons.extend(copy.deepcopy(envelope_reasons))
    if context is not None:
        overlay_state = context["overlay_selection_state"]
        for kind in ("institutional", "funder"):
            if overlay_state[kind] == "not_provided":
                reasons.append(
                    {
                        "status": "APPLICABILITY_UNRESOLVED",
                        "code": "OVERLAY_SELECTION_NOT_PROVIDED",
                        "fact_id": None,
                        "overlay_kind": kind,
                    }
                )
    reasons.sort(
        key=lambda row: (
            row["code"],
            row["fact_id"] or "",
            row["overlay_kind"] or "",
        )
    )
    return reasons


def _observation_by_id(
    observations: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {row["artifact_id"]: row for row in observations}


def _inventory_indexes(
    inventory: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], list[str]],
    dict[str, dict[str, Any]],
]:
    """Index bounded inventory joins once; entry expansion must never rescan it."""
    artifacts_by_id: dict[str, dict[str, Any]] = {}
    artifacts_by_evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
    evidence_ids_by_artifact_requirement: dict[tuple[str, str], list[str]] = {}
    for artifact in inventory["artifacts"]:
        artifact_id = artifact["artifact_id"]
        artifacts_by_id[artifact_id] = artifact
        for binding in artifact["evidence_bindings"]:
            requirement_id = binding["requirement_id"]
            evidence_id = binding["evidence_id"]
            artifacts_by_evidence.setdefault(
                (requirement_id, evidence_id), []
            ).append(artifact)
            evidence_ids_by_artifact_requirement.setdefault(
                (artifact_id, requirement_id), []
            ).append(evidence_id)
    for artifacts in artifacts_by_evidence.values():
        artifacts.sort(key=lambda row: row["artifact_id"])
    for evidence_ids in evidence_ids_by_artifact_requirement.values():
        evidence_ids.sort()
    claims_by_requirement = {
        claim["requirement_id"]: claim
        for claim in inventory["waiver_or_exception_claims"]
    }
    return (
        artifacts_by_id,
        artifacts_by_evidence,
        evidence_ids_by_artifact_requirement,
        claims_by_requirement,
    )


def _resolved_requirement(
    result: dict[str, Any], registry: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    requirement = _pointer_get(
        registry, result["requirement_pointer"], "resolved.requirement_pointer"
    )
    if requirement.get("requirement_id") != result["requirement_id"]:
        _fail("resolved.requirement_pointer", "does not identify its requirement_id")
    if _digest(requirement) != result["requirement_digest"]:
        _fail("resolved.requirement_digest", "does not match the pointed requirement")
    evidence_rows = requirement.get("evidence_expected")
    if not isinstance(evidence_rows, list):
        _fail("resolved.requirement_pointer", "has no mechanical evidence roster")
    if any(not isinstance(row, dict) for row in evidence_rows):
        _fail("resolved.requirement_pointer", "has a malformed evidence pointer")
    return requirement, evidence_rows


def _artifact_conflict_reasons(
    artifact: dict[str, Any],
    evidence: dict[str, Any],
    observation: dict[str, Any],
) -> list[str]:
    reasons = (
        list(observation["reason_codes"])
        if observation["status"] == "CONFLICTING"
        else []
    )
    if observation["state"] != "located":
        return sorted(set(reasons))
    if artifact["artifact_type"] != evidence["artifact_type"]:
        reasons.append("ARTIFACT_TYPE_MISMATCH")
    if artifact["declared_holder_role_id"] != evidence["held_by"]:
        reasons.append("ARTIFACT_HOLDER_MISMATCH")

    structure = artifact["declared_structure"]
    certificate = structure["certificate"]
    if certificate is not None and (
        certificate["holder_role_id"] != evidence["held_by"]
        or certificate["holder_role_id"] != artifact["declared_holder_role_id"]
    ):
        reasons.append("CERTIFICATE_HOLDER_MISMATCH")
    return sorted(set(reasons))


def _located_profiled_route_claim(
    requirement_id: str,
    requirement: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    registry: dict[str, Any],
    scoped_by_id: dict[str, dict[str, Any]],
    responsibility_roles: set[str],
    artifacts_by_id: dict[str, dict[str, Any]],
    artifacts_by_evidence: dict[tuple[str, str], list[dict[str, Any]]],
    evidence_ids_by_artifact_requirement: dict[tuple[str, str], list[str]],
    claims_by_requirement: dict[str, dict[str, Any]],
    resolved_requirements: dict[
        str, tuple[dict[str, Any], list[dict[str, Any]]]
    ],
    evidence_by_requirement: dict[str, dict[str, dict[str, Any]]],
) -> bool:
    route = requirement.get("waiver_or_exception_route")
    if not isinstance(route, dict) or route.get("state") != "profiled":
        return False
    profiled_ids = route.get("requirement_ids")
    if not isinstance(profiled_ids, list) or not profiled_ids:
        return False
    claim = claims_by_requirement.get(requirement_id)
    if claim is None or set(claim["route_requirement_ids"]) != set(
        profiled_ids
    ) or len(claim["route_requirement_ids"]) != len(profiled_ids):
        return False
    artifact_id = claim["decision_artifact_id"]
    if artifact_id is None:
        return False
    observation = observations.get(artifact_id)
    artifact = artifacts_by_id.get(artifact_id)
    if artifact is None or observation is None or observation["state"] != "located":
        return False

    for route_requirement_id in profiled_ids:
        route_result = scoped_by_id.get(route_requirement_id)
        if (
            route_result is None
            or route_result["applicability"] != "true"
            or "submission_packet" not in route_result["consumer_scopes"]
            or route_result["obligated_actor"] not in responsibility_roles
        ):
            return False
        if route_requirement_id not in resolved_requirements:
            resolved_requirements[route_requirement_id] = _resolved_requirement(
                route_result, registry
            )
        if route_requirement_id not in evidence_by_requirement:
            evidence_by_requirement[route_requirement_id] = {
                row["evidence_id"]: row
                for row in resolved_requirements[route_requirement_id][1]
            }
        evidence_by_id = evidence_by_requirement[route_requirement_id]
        bound_evidence_ids = evidence_ids_by_artifact_requirement.get(
            (artifact_id, route_requirement_id), []
        )
        route_evidence_documented = False
        for evidence_id in bound_evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if (
                evidence is None
                or evidence["held_by"] not in responsibility_roles
                or artifacts_by_evidence.get(
                    (route_requirement_id, evidence_id), []
                )
                != [artifact]
            ):
                continue
            if not _artifact_conflict_reasons(artifact, evidence, observation):
                route_evidence_documented = True
                break
        if not route_evidence_documented:
            return False
    return True


def _packet_owned_entry_state(
    *,
    requirement_id: str,
    evidence: dict[str, Any],
    requirement: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    registry: dict[str, Any],
    scoped_by_id: dict[str, dict[str, Any]],
    responsibility_roles: set[str],
    artifacts_by_evidence: dict[tuple[str, str], list[dict[str, Any]]],
    route_claim_results: dict[str, bool],
    artifacts_by_id: dict[str, dict[str, Any]],
    evidence_ids_by_artifact_requirement: dict[tuple[str, str], list[str]],
    claims_by_requirement: dict[str, dict[str, Any]],
    resolved_requirements: dict[
        str, tuple[dict[str, Any], list[dict[str, Any]]]
    ],
    evidence_by_requirement: dict[str, dict[str, dict[str, Any]]],
) -> tuple[str, str, list[str], list[str]]:
    matches = artifacts_by_evidence.get((requirement_id, evidence["evidence_id"]), [])
    matched_ids = [row["artifact_id"] for row in matches]
    if not matches:
        if requirement_id not in route_claim_results:
            route_claim_results[requirement_id] = _located_profiled_route_claim(
                requirement_id,
                requirement,
                observations,
                registry,
                scoped_by_id,
                responsibility_roles,
                artifacts_by_id,
                artifacts_by_evidence,
                evidence_ids_by_artifact_requirement,
                claims_by_requirement,
                resolved_requirements,
                evidence_by_requirement,
            )
        if route_claim_results[requirement_id]:
            return (
                "ACCEPTANCE_UNVERIFIED",
                "unresolved",
                ["WAIVER_OR_EXCEPTION_CLAIM_UNVERIFIED"],
                [],
            )
        return (
            "NOT_LOCATED",
            "gap",
            ["EXPECTED_PACKET_ARTIFACT_NOT_LOCATED"],
            [],
        )
    if len(matches) > 1:
        return (
            "CONFLICTING",
            "gap",
            ["DUPLICATE_EVIDENCE_BINDING"],
            matched_ids,
        )

    artifact = matches[0]
    observation = observations[artifact["artifact_id"]]
    if observation["state"] != "located":
        return (
            "CONFLICTING",
            "gap",
            list(observation["reason_codes"]),
            matched_ids,
        )

    reasons = _artifact_conflict_reasons(
        artifact, evidence, observation
    )
    if reasons:
        return "CONFLICTING", "gap", reasons, matched_ids
    return "DOCUMENTED", "none", ["STRUCTURE_DOCUMENTED"], matched_ids


def _evidence_entries(
    inventory: dict[str, Any],
    context: dict[str, Any],
    registry: dict[str, Any],
    resolved: dict[str, Any],
    observations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scoped: list[dict[str, Any]] = []
    for row in resolved["requirement_results"]:
        if "submission_packet" not in row["consumer_scopes"]:
            continue
        if len(row["consumer_scopes"]) > MAX_CONSUMER_SCOPES:
            _fail(
                "resolved.requirement_results",
                f"submission-packet consumer scopes exceed {MAX_CONSUMER_SCOPES} items",
            )
        scoped.append(row)
    scoped.sort(
        key=lambda row: (
            row["axis"],
            row["authority_kind"],
            row["authority_id"],
            row["requirement_id"],
        )
    )
    scoped_by_id: dict[str, dict[str, Any]] = {}
    for row in scoped:
        if row["requirement_id"] in scoped_by_id:
            _fail(
                "resolved.requirement_results",
                f"duplicate submission-packet requirement_id: {row['requirement_id']}",
            )
        scoped_by_id[row["requirement_id"]] = row
    entries_with_order: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    excluded: list[dict[str, Any]] = []
    observed_by_id = _observation_by_id(observations)
    responsibility_roles = set(inventory["packet_responsibility_role_ids"])
    (
        artifacts_by_id,
        artifacts_by_evidence,
        evidence_ids_by_artifact_requirement,
        claims_by_requirement,
    ) = _inventory_indexes(inventory)
    resolved_requirements: dict[
        str, tuple[dict[str, Any], list[dict[str, Any]]]
    ] = {}
    evidence_by_requirement: dict[str, dict[str, dict[str, Any]]] = {}
    route_claim_results: dict[str, bool] = {}

    for result in scoped:
        reference = _requirement_ref(result)
        if result["applicability"] == "false":
            if len(excluded) >= MAX_EXCLUDED_REQUIREMENTS:
                _fail(
                    "resolved.requirement_results",
                    f"exceeds {MAX_EXCLUDED_REQUIREMENTS} excluded submission-packet requirements",
                )
            excluded.append(
                {
                    "requirement_ref": reference,
                    "exclusion_basis": "resolved_predicate_false",
                }
            )
            continue
        if result["applicability"] != "true":
            _fail(
                "resolved.requirement_results",
                "a permitted downstream gate may contain only true or false applicability",
            )
        requirement_id = result["requirement_id"]
        if requirement_id not in resolved_requirements:
            resolved_requirements[requirement_id] = _resolved_requirement(
                result, registry
            )
        requirement, evidence_rows = resolved_requirements[requirement_id]
        for evidence_index, evidence in enumerate(evidence_rows):
            if len(entries_with_order) >= MAX_MANIFEST_ENTRIES:
                _fail(
                    "resolved.requirement_results",
                    f"exceeds {MAX_MANIFEST_ENTRIES} submission-packet evidence entries",
                )
            evidence_id = evidence.get("evidence_id")
            artifact_type = evidence.get("artifact_type")
            held_by = evidence.get("held_by")
            _identifier(evidence_id, "registry.evidence_expected.evidence_id")
            _identifier(artifact_type, "registry.evidence_expected.artifact_type")
            _identifier(held_by, "registry.evidence_expected.held_by")
            evidence_ref = {
                "evidence_id": evidence_id,
                "evidence_pointer": (
                    f"{result['requirement_pointer']}/evidence_expected/{evidence_index}"
                ),
                "evidence_digest": _digest(evidence),
                "artifact_type": artifact_type,
                "held_by": held_by,
            }
            matched = artifacts_by_evidence.get(
                (result["requirement_id"], evidence_id), []
            )
            matched_ids = [row["artifact_id"] for row in matched]
            packet_owned = (
                held_by in responsibility_roles
                and result["obligated_actor"] in responsibility_roles
            )
            if not packet_owned:
                status = "ACCEPTANCE_UNVERIFIED"
                readiness_effect = "none"
                reason_codes = ["EXTERNAL_HOLDER_DEPENDENCY"]
            else:
                status, readiness_effect, reason_codes, matched_ids = (
                    _packet_owned_entry_state(
                        requirement_id=result["requirement_id"],
                        evidence=evidence,
                        requirement=requirement,
                        observations=observed_by_id,
                        registry=registry,
                        scoped_by_id=scoped_by_id,
                        responsibility_roles=responsibility_roles,
                        artifacts_by_evidence=artifacts_by_evidence,
                        route_claim_results=route_claim_results,
                        artifacts_by_id=artifacts_by_id,
                        evidence_ids_by_artifact_requirement=(
                            evidence_ids_by_artifact_requirement
                        ),
                        claims_by_requirement=claims_by_requirement,
                        resolved_requirements=resolved_requirements,
                        evidence_by_requirement=evidence_by_requirement,
                    )
                )
            entries_with_order.append(
                (
                    (
                        result["axis"],
                        result["authority_kind"],
                        result["authority_id"],
                        result["requirement_id"],
                        evidence_ref["evidence_pointer"],
                    ),
                    {
                        "requirement_ref": reference,
                        "evidence_ref": evidence_ref,
                        "responsibility": (
                            "packet_owned"
                            if packet_owned
                            else "external_dependency"
                        ),
                        "status": status,
                        "readiness_effect": readiness_effect,
                        "reason_codes": reason_codes,
                        "matched_artifact_ids": matched_ids,
                    },
                )
            )
    entries_with_order.sort(key=lambda item: item[0])
    excluded.sort(
        key=lambda row: (
            row["requirement_ref"]["axis"],
            row["requirement_ref"]["authority_kind"],
            row["requirement_ref"]["authority_id"],
            row["requirement_ref"]["requirement_id"],
        )
    )
    return [item[1] for item in entries_with_order], excluded


def _readiness(
    unresolved_reasons: list[dict[str, Any]], entries: list[dict[str, Any]]
) -> str:
    if unresolved_reasons or any(
        row["readiness_effect"] == "unresolved" for row in entries
    ):
        return "unresolved"
    if any(row["readiness_effect"] == "gap" for row in entries):
        return "gaps_located"
    return "no_listed_gaps_located"


def build_submission_packet_manifest(
    inventory: dict[str, Any],
    packet_root: Path | str,
    *,
    context: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    resolved: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a manifest; a supplied authority triplet is replayed before dereference."""
    supplied = (context is not None, registry is not None, resolved is not None)
    if any(supplied) and not all(supplied):
        raise ContractError("context, registry, and resolved authority inputs are all-or-none")

    # This replay is deliberately the first semantic operation on a complete
    # authority triplet.  A failure stops before packet or authority pointers
    # are dereferenced by this layer.
    if all(supplied):
        assert context is not None and registry is not None and resolved is not None
        validate_resolved_context(resolved, context, registry)

    validate_submission_packet_inventory(inventory)
    binding = _authority_binding(resolved)
    envelope, envelope_reasons = _capability_envelope(context)
    overlay_state = (
        copy.deepcopy(context["overlay_selection_state"])
        if context is not None
        else None
    )
    unresolved_reasons = _global_unresolved_reasons(
        resolved=resolved,
        context=context,
        envelope_reasons=envelope_reasons,
    )

    gate_allowed = bool(
        resolved is not None
        and resolved["resolution_state"] == "resolved"
        and resolved["downstream_gate"]["profile_dependent_result_allowed"]
    )
    within_envelope = envelope["state"] == "within_v1"
    if gate_allowed and within_envelope:
        assert context is not None and registry is not None and resolved is not None
        observations = observe_submission_packet(inventory, packet_root)
        entries, excluded = _evidence_entries(
            inventory, context, registry, resolved, observations
        )
    else:
        # Fail-closed states intentionally do not touch packet_root or follow
        # registry pointers.  The empty observation digest proves that scope.
        observations = []
        entries = []
        excluded = []

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "inventory_pointer": {
            "inventory_id": inventory["inventory_id"],
            "schema_version": inventory["schema_version"],
            "inventory_digest": _digest(_semantic_inventory(inventory)),
        },
        "authority_binding": binding,
        "packet_pointer": {
            "scope": "explicit_inventory_paths_only",
            "observation_digest": _digest(observations),
        },
        "packet_observations": observations,
        "capability_envelope": envelope,
        "overlay_selection_state": overlay_state,
        "administrative_status": {
            "review_pathway": REVIEW_PATHWAY,
            "submission_readiness": _readiness(unresolved_reasons, entries),
            "authorization_status": copy.deepcopy(
                inventory["authorization_status_input"]
            ),
            "review_timeline": REVIEW_TIMELINE,
        },
        "acceptance_boundary": {
            "status": "ACCEPTANCE_UNVERIFIED",
            "reason_code": ACCEPTANCE_REASON,
            "affects_submission_readiness": False,
        },
        "entries": entries,
        "excluded_requirements": excluded,
        "unresolved_reasons": unresolved_reasons,
        "boundary_footer": BOUNDARY_FOOTER,
    }
    manifest["manifest_digest"] = _digest(manifest)
    _enforce_manifest_byte_limit(manifest)
    return manifest


def _validate_authorization_status(value: Any, path: str) -> None:
    row = _closed(value, path, {"value", "source_reference", "provenance"})
    if row["value"] not in AUTHORIZATION_VALUES:
        _fail(f"{path}.value", "has an invalid authorization input status")
    if row["provenance"] != "caller_supplied_no_derivation":
        _fail(f"{path}.provenance", "must equal caller_supplied_no_derivation")
    if row["value"] == "documented":
        _identifier(row["source_reference"], f"{path}.source_reference")
    elif row["source_reference"] is not None:
        _fail(f"{path}.source_reference", "must be null for this status")


def _validate_context_pointer(value: Any, path: str) -> None:
    row = _closed(
        value, path, {"context_record_id", "schema_version", "context_digest"}
    )
    _identifier(row["context_record_id"], f"{path}.context_record_id")
    if row["schema_version"] != "irb-context-record/1.0":
        _fail(f"{path}.schema_version", "must equal irb-context-record/1.0")
    _sha(row["context_digest"], f"{path}.context_digest")


def _validate_registry_pointer(value: Any, path: str) -> None:
    row = _closed(
        value,
        path,
        {"registry_id", "registry_version", "as_of", "registry_digest"},
    )
    _identifier(row["registry_id"], f"{path}.registry_id")
    _version(row["registry_version"], f"{path}.registry_version")
    _iso_date(row["as_of"], f"{path}.as_of")
    _sha(row["registry_digest"], f"{path}.registry_digest")


def _validate_downstream_gate(value: Any, path: str) -> dict[str, Any]:
    row = _closed(
        value,
        path,
        {
            "both_axes_selected",
            "exact_selection_resolved",
            "all_applicability_resolved",
            "profile_dependent_result_allowed",
        },
    )
    for field, field_value in row.items():
        if not isinstance(field_value, bool):
            _fail(f"{path}.{field}", "must be boolean")
    return row


def _validate_requirement_ref(value: Any, path: str, applicability: str) -> None:
    row = _closed(value, path, set(_REQUIREMENT_REF_FIELDS))
    _identifier(row["requirement_id"], f"{path}.requirement_id")
    if row["authority_kind"] not in {
        "profile",
        "institutional_overlay",
        "funder_overlay",
    }:
        _fail(f"{path}.authority_kind", "has an invalid authority kind")
    _identifier(row["authority_id"], f"{path}.authority_id")
    _version(row["authority_version"], f"{path}.authority_version")
    _sha(row["authority_digest"], f"{path}.authority_digest")
    if row["axis"] not in {"review_ethics", "data_protection"}:
        _fail(f"{path}.axis", "has an invalid authority axis")
    _identifier(row["obligated_actor"], f"{path}.obligated_actor")
    scopes = _unique_identifiers(
        row["consumer_scopes"],
        f"{path}.consumer_scopes",
        maximum=MAX_CONSUMER_SCOPES,
        minimum=1,
    )
    if "submission_packet" not in scopes:
        _fail(f"{path}.consumer_scopes", "must include submission_packet")
    if row["applicability"] != applicability:
        _fail(f"{path}.applicability", f"must equal {applicability}")
    _sha(row["requirement_digest"], f"{path}.requirement_digest")
    pointer = row["requirement_pointer"]
    if not isinstance(pointer, str) or re.fullmatch(
        r"/(profiles|overlays)/[0-9]+/requirements/[0-9]+", pointer
    ) is None:
        _fail(f"{path}.requirement_pointer", "has an invalid exact pointer")
    if row["authority_anchor_pointer"] != f"{pointer}/authority_anchor":
        _fail(
            f"{path}.authority_anchor_pointer",
            "must identify the anchor below requirement_pointer",
        )


def _validate_evidence_ref(value: Any, path: str, requirement_pointer: str) -> None:
    row = _closed(
        value,
        path,
        {"evidence_id", "evidence_pointer", "evidence_digest", "artifact_type", "held_by"},
    )
    _identifier(row["evidence_id"], f"{path}.evidence_id")
    pointer = row["evidence_pointer"]
    if not isinstance(pointer, str) or re.fullmatch(
        re.escape(requirement_pointer) + r"/evidence_expected/[0-9]+", pointer
    ) is None:
        _fail(f"{path}.evidence_pointer", "must be below its requirement pointer")
    _sha(row["evidence_digest"], f"{path}.evidence_digest")
    _identifier(row["artifact_type"], f"{path}.artifact_type")
    _identifier(row["held_by"], f"{path}.held_by")


def _validate_manifest_shape(manifest: dict[str, Any]) -> None:
    root = _closed(
        manifest,
        "manifest",
        {
            "schema_version",
            "inventory_pointer",
            "authority_binding",
            "packet_pointer",
            "packet_observations",
            "capability_envelope",
            "overlay_selection_state",
            "administrative_status",
            "acceptance_boundary",
            "entries",
            "excluded_requirements",
            "unresolved_reasons",
            "boundary_footer",
            "manifest_digest",
        },
    )
    _enforce_manifest_byte_limit(root)
    if root["schema_version"] != MANIFEST_SCHEMA_VERSION:
        _fail("manifest.schema_version", f"must equal {MANIFEST_SCHEMA_VERSION}")
    claimed_digest = _sha(root["manifest_digest"], "manifest.manifest_digest")
    unsigned = copy.deepcopy(root)
    unsigned.pop("manifest_digest")
    if _digest(unsigned) != claimed_digest:
        _fail(
            "manifest.manifest_digest",
            "does not match the canonical artifact digest with itself excluded",
        )

    inventory_pointer = _closed(
        root["inventory_pointer"],
        "manifest.inventory_pointer",
        {"inventory_id", "schema_version", "inventory_digest"},
    )
    _identifier(inventory_pointer["inventory_id"], "manifest.inventory_pointer.inventory_id")
    if inventory_pointer["schema_version"] != INVENTORY_SCHEMA_VERSION:
        _fail(
            "manifest.inventory_pointer.schema_version",
            f"must equal {INVENTORY_SCHEMA_VERSION}",
        )
    _sha(
        inventory_pointer["inventory_digest"],
        "manifest.inventory_pointer.inventory_digest",
    )

    authority = _closed(
        root["authority_binding"],
        "manifest.authority_binding",
        {
            "state",
            "context_pointer",
            "registry_pointer",
            "resolved_digest",
            "resolution_state",
            "downstream_gate",
        },
    )
    if authority["state"] == "not_provided":
        for field in (
            "context_pointer",
            "registry_pointer",
            "resolved_digest",
            "resolution_state",
            "downstream_gate",
        ):
            if authority[field] is not None:
                _fail(f"manifest.authority_binding.{field}", "must be null")
    elif authority["state"] == "replay_validated":
        _validate_context_pointer(
            authority["context_pointer"], "manifest.authority_binding.context_pointer"
        )
        _validate_registry_pointer(
            authority["registry_pointer"], "manifest.authority_binding.registry_pointer"
        )
        _sha(authority["resolved_digest"], "manifest.authority_binding.resolved_digest")
        if authority["resolution_state"] not in {
            "resolved",
            "jurisdiction_unresolved",
            "applicability_unresolved",
        }:
            _fail(
                "manifest.authority_binding.resolution_state",
                "has an invalid resolution state",
            )
        gate = _validate_downstream_gate(
            authority["downstream_gate"], "manifest.authority_binding.downstream_gate"
        )
        if authority["resolution_state"] == "resolved":
            if gate != {
                "both_axes_selected": True,
                "exact_selection_resolved": True,
                "all_applicability_resolved": True,
                "profile_dependent_result_allowed": True,
            }:
                _fail(
                    "manifest.authority_binding.downstream_gate",
                    "must be fully open when resolution_state is resolved",
                )
        elif gate["profile_dependent_result_allowed"] is not False:
            _fail(
                "manifest.authority_binding.downstream_gate.profile_dependent_result_allowed",
                "must be false when authority resolution is unresolved",
            )
    else:
        _fail("manifest.authority_binding.state", "has an invalid binding state")

    packet_pointer = _closed(
        root["packet_pointer"],
        "manifest.packet_pointer",
        {"scope", "observation_digest"},
    )
    if packet_pointer["scope"] != "explicit_inventory_paths_only":
        _fail(
            "manifest.packet_pointer.scope", "must equal explicit_inventory_paths_only"
        )
    _sha(packet_pointer["observation_digest"], "manifest.packet_pointer.observation_digest")
    observations = _array(root["packet_observations"], "manifest.packet_observations")
    observation_ids: set[str] = set()
    observation_paths: set[str] = set()
    for index, raw_observation in enumerate(observations):
        path = f"manifest.packet_observations[{index}]"
        observation = _closed(
            raw_observation,
            path,
            {
                "artifact_id",
                "relative_path",
                "state",
                "observed_sha256",
                "observed_size_bytes",
                "status",
                "reason_codes",
            },
        )
        artifact_id = _identifier(observation["artifact_id"], f"{path}.artifact_id")
        relative_path = _relative_path(observation["relative_path"], f"{path}.relative_path")
        if artifact_id in observation_ids or relative_path in observation_paths:
            _fail(path, "duplicates an observation identity or path")
        observation_ids.add(artifact_id)
        observation_paths.add(relative_path)
        if observation["state"] == "located":
            _sha(observation["observed_sha256"], f"{path}.observed_sha256")
            size = observation["observed_size_bytes"]
            if isinstance(size, bool) or not isinstance(size, int) or not 0 <= size <= MAX_ARTIFACT_BYTES:
                _fail(f"{path}.observed_size_bytes", "has an invalid observed size")
        elif observation["state"] == "not_located":
            if observation["observed_sha256"] is not None or observation["observed_size_bytes"] is not None:
                _fail(path, "a not_located observation cannot carry observed values")
        else:
            _fail(f"{path}.state", "must be located or not_located")
        if observation["status"] not in {"DOCUMENTED", "CONFLICTING"}:
            _fail(f"{path}.status", "must be DOCUMENTED or CONFLICTING")
        observation_reasons = observation["reason_codes"]
        if (
            not isinstance(observation_reasons, list)
            or not observation_reasons
            or any(not isinstance(reason, str) for reason in observation_reasons)
            or len(set(observation_reasons)) != len(observation_reasons)
            or any(
                reason not in OBSERVATION_REASON_CODES
                for reason in observation_reasons
            )
            or observation_reasons != sorted(observation_reasons)
        ):
            _fail(f"{path}.reason_codes", "has invalid or non-canonical reasons")
        if observation["state"] == "not_located":
            if (
                observation["status"] != "CONFLICTING"
                or observation_reasons != ["DECLARED_ATTACHMENT_NOT_LOCATED"]
            ):
                _fail(path, "not_located must preserve its exact declared conflict")
        elif observation["status"] == "DOCUMENTED":
            if observation_reasons != ["STRUCTURE_DOCUMENTED"]:
                _fail(path, "DOCUMENTED must carry STRUCTURE_DOCUMENTED only")
        elif any(
            reason
            in {"STRUCTURE_DOCUMENTED", "DECLARED_ATTACHMENT_NOT_LOCATED"}
            for reason in observation_reasons
        ):
            _fail(path, "a located conflict has an invalid reason")
    if _digest(observations) != packet_pointer["observation_digest"]:
        _fail(
            "manifest.packet_pointer.observation_digest",
            "does not match the canonical packet observations",
        )
    if observations != sorted(
        observations, key=lambda row: (row["artifact_id"], row["relative_path"])
    ):
        _fail("manifest.packet_observations", "must use canonical artifact/path order")

    envelope = _closed(
        root["capability_envelope"],
        "manifest.capability_envelope",
        {"state", "facts", "reason_codes"},
    )
    fact_rows = _array(
        envelope["facts"], "manifest.capability_envelope.facts", maximum=7, minimum=7
    )
    expected_values = dict(ENVELOPE_FACTS)
    fact_ids: set[str] = set()
    derived_envelope_reasons: list[str] = []
    for index, raw_fact in enumerate(fact_rows):
        path = f"manifest.capability_envelope.facts[{index}]"
        fact = _closed(
            raw_fact,
            path,
            {"fact_id", "required_value", "declared_state", "declared_value"},
        )
        fact_id = fact["fact_id"]
        if fact_id not in expected_values or fact_id in fact_ids:
            _fail(f"{path}.fact_id", "must identify one unique V1 envelope fact")
        fact_ids.add(fact_id)
        if fact["required_value"] is not expected_values[fact_id]:
            _fail(f"{path}.required_value", "does not match the V1 envelope")
        if fact["declared_state"] == "declared":
            if not isinstance(fact["declared_value"], bool):
                _fail(f"{path}.declared_value", "must be boolean when declared")
            if fact["declared_value"] != fact["required_value"]:
                reason = "V1_ENVELOPE_OUTSIDE"
            else:
                reason = None
        elif fact["declared_state"] == "unknown":
            if fact["declared_value"] is not None:
                _fail(f"{path}.declared_value", "must be null when unknown")
            reason = "V1_ENVELOPE_FACT_UNKNOWN"
        elif fact["declared_state"] == "missing":
            if fact["declared_value"] is not None:
                _fail(f"{path}.declared_value", "must be null when missing")
            reason = "V1_ENVELOPE_FACT_MISSING"
        else:
            _fail(f"{path}.declared_state", "has an invalid declaration state")
        if reason is not None and reason not in derived_envelope_reasons:
            derived_envelope_reasons.append(reason)
    if [row["fact_id"] for row in fact_rows] != [row[0] for row in ENVELOPE_FACTS]:
        _fail(
            "manifest.capability_envelope.facts",
            "must use the fixed V1 envelope fact order",
        )
    envelope_reasons = envelope["reason_codes"]
    if not isinstance(envelope_reasons, list) or envelope_reasons != derived_envelope_reasons:
        _fail(
            "manifest.capability_envelope.reason_codes",
            "must exactly summarize the ordered fact states",
        )
    expected_envelope_state = "within_v1" if not envelope_reasons else "unresolved"
    if envelope["state"] != expected_envelope_state:
        _fail("manifest.capability_envelope.state", "does not match its fact states")

    overlay = root["overlay_selection_state"]
    if overlay is not None:
        overlay = _closed(
            overlay,
            "manifest.overlay_selection_state",
            {"institutional", "funder"},
        )
        for kind in ("institutional", "funder"):
            if overlay[kind] not in {
                "selected",
                "not_provided",
                "none_declared_by_author",
            }:
                _fail(f"manifest.overlay_selection_state.{kind}", "has an invalid state")
    if authority["state"] == "not_provided" and overlay is not None:
        _fail(
            "manifest.overlay_selection_state",
            "must be null when authority inputs are not provided",
        )
    if authority["state"] == "replay_validated" and overlay is None:
        _fail(
            "manifest.overlay_selection_state",
            "must be present when authority inputs are replay validated",
        )

    administrative = _closed(
        root["administrative_status"],
        "manifest.administrative_status",
        {
            "review_pathway",
            "submission_readiness",
            "authorization_status",
            "review_timeline",
        },
    )
    if administrative["review_pathway"] != REVIEW_PATHWAY:
        _fail("manifest.administrative_status.review_pathway", "has changed")
    if administrative["submission_readiness"] not in READINESS_VALUES:
        _fail("manifest.administrative_status.submission_readiness", "has an invalid state")
    _validate_authorization_status(
        administrative["authorization_status"],
        "manifest.administrative_status.authorization_status",
    )
    if administrative["review_timeline"] != REVIEW_TIMELINE:
        _fail("manifest.administrative_status.review_timeline", "has changed")

    acceptance = _closed(
        root["acceptance_boundary"],
        "manifest.acceptance_boundary",
        {"status", "reason_code", "affects_submission_readiness"},
    )
    if acceptance != {
        "status": "ACCEPTANCE_UNVERIFIED",
        "reason_code": ACCEPTANCE_REASON,
        "affects_submission_readiness": False,
    }:
        _fail("manifest.acceptance_boundary", "must preserve the fixed acceptance boundary")

    entries = _array(root["entries"], "manifest.entries", maximum=4096)
    for index, raw_entry in enumerate(entries):
        path = f"manifest.entries[{index}]"
        entry = _closed(
            raw_entry,
            path,
            {
                "requirement_ref",
                "evidence_ref",
                "responsibility",
                "status",
                "readiness_effect",
                "reason_codes",
                "matched_artifact_ids",
            },
        )
        _validate_requirement_ref(entry["requirement_ref"], f"{path}.requirement_ref", "true")
        _validate_evidence_ref(
            entry["evidence_ref"],
            f"{path}.evidence_ref",
            entry["requirement_ref"]["requirement_pointer"],
        )
        if entry["responsibility"] not in {"packet_owned", "external_dependency"}:
            _fail(f"{path}.responsibility", "has an invalid responsibility")
        if entry["status"] not in STATUSES:
            _fail(f"{path}.status", "has an invalid status")
        if entry["readiness_effect"] not in {"none", "gap", "unresolved"}:
            _fail(f"{path}.readiness_effect", "has an invalid readiness effect")
        reason_codes = entry["reason_codes"]
        if not isinstance(reason_codes, list) or not 1 <= len(reason_codes) <= 16:
            _fail(f"{path}.reason_codes", "must be a non-empty bounded array")
        if any(not isinstance(code, str) for code in reason_codes) or len(
            set(reason_codes)
        ) != len(reason_codes) or any(
            code not in ENTRY_REASON_CODES for code in reason_codes
        ):
            _fail(f"{path}.reason_codes", "contains a duplicate or invalid reason")
        if reason_codes != sorted(reason_codes):
            _fail(f"{path}.reason_codes", "must use canonical reason-code order")
        _unique_identifiers(
            entry["matched_artifact_ids"], f"{path}.matched_artifact_ids"
        )
        if entry["matched_artifact_ids"] != sorted(entry["matched_artifact_ids"]):
            _fail(f"{path}.matched_artifact_ids", "must use canonical identifier order")
        if entry["status"] == "DOCUMENTED" and (
            entry["responsibility"], entry["readiness_effect"]
        ) != ("packet_owned", "none"):
            _fail(path, "DOCUMENTED must be packet-owned with no readiness effect")
        if entry["status"] in {"NOT_LOCATED", "CONFLICTING"} and (
            entry["responsibility"], entry["readiness_effect"]
        ) != ("packet_owned", "gap"):
            _fail(path, "a located packet gap must remain packet-owned")
        if entry["status"] == "APPLICABILITY_UNRESOLVED" and entry[
            "readiness_effect"
        ] != "unresolved":
            _fail(path, "unresolved applicability must leave readiness unresolved")
        if entry["status"] == "ACCEPTANCE_UNVERIFIED":
            expected = (
                "none" if entry["responsibility"] == "external_dependency" else "unresolved"
            )
            if entry["readiness_effect"] != expected:
                _fail(path, "acceptance state has an invalid readiness effect")
    entry_keys = [
        (
            row["requirement_ref"]["axis"],
            row["requirement_ref"]["authority_kind"],
            row["requirement_ref"]["authority_id"],
            row["requirement_ref"]["requirement_id"],
            row["evidence_ref"]["evidence_pointer"],
        )
        for row in entries
    ]
    if entry_keys != sorted(entry_keys) or len(set(entry_keys)) != len(entry_keys):
        _fail("manifest.entries", "must use unique canonical semantic order")

    excluded = _array(
        root["excluded_requirements"], "manifest.excluded_requirements", maximum=4096
    )
    for index, raw_excluded in enumerate(excluded):
        path = f"manifest.excluded_requirements[{index}]"
        row = _closed(raw_excluded, path, {"requirement_ref", "exclusion_basis"})
        _validate_requirement_ref(row["requirement_ref"], f"{path}.requirement_ref", "false")
        if row["exclusion_basis"] != "resolved_predicate_false":
            _fail(f"{path}.exclusion_basis", "has changed")
    excluded_keys = [
        (
            row["requirement_ref"]["axis"],
            row["requirement_ref"]["authority_kind"],
            row["requirement_ref"]["authority_id"],
            row["requirement_ref"]["requirement_id"],
        )
        for row in excluded
    ]
    if excluded_keys != sorted(excluded_keys) or len(set(excluded_keys)) != len(
        excluded_keys
    ):
        _fail("manifest.excluded_requirements", "must use unique canonical order")

    unresolved = _array(
        root["unresolved_reasons"], "manifest.unresolved_reasons", maximum=128
    )
    if len({_canonical_bytes(row) for row in unresolved}) != len(unresolved):
        _fail("manifest.unresolved_reasons", "contains a duplicate reason")
    for index, raw_reason in enumerate(unresolved):
        path = f"manifest.unresolved_reasons[{index}]"
        reason = _closed(raw_reason, path, {"status", "code", "fact_id", "overlay_kind"})
        if reason["status"] != "APPLICABILITY_UNRESOLVED":
            _fail(f"{path}.status", "must equal APPLICABILITY_UNRESOLVED")
        if reason["code"] not in GLOBAL_REASON_CODES:
            _fail(f"{path}.code", "has an invalid unresolved reason")
        if reason["fact_id"] is not None:
            _identifier(reason["fact_id"], f"{path}.fact_id")
        if reason["overlay_kind"] not in {None, "institutional", "funder"}:
            _fail(f"{path}.overlay_kind", "has an invalid overlay kind")

    expected_unresolved: list[dict[str, Any]] = []
    gate_permitted = bool(
        authority["state"] == "replay_validated"
        and authority["resolution_state"] == "resolved"
        and authority["downstream_gate"]["profile_dependent_result_allowed"]
    )
    if authority["state"] == "not_provided":
        expected_unresolved.append(
            {
                "status": "APPLICABILITY_UNRESOLVED",
                "code": "AUTHORITY_INPUT_NOT_PROVIDED",
                "fact_id": None,
                "overlay_kind": None,
            }
        )
    elif not gate_permitted:
        expected_unresolved.append(
            {
                "status": "APPLICABILITY_UNRESOLVED",
                "code": "AUTHORITY_RESOLUTION_NOT_PERMITTED",
                "fact_id": None,
                "overlay_kind": None,
            }
        )
    for fact in fact_rows:
        if fact["declared_state"] == "missing":
            code = "V1_ENVELOPE_FACT_MISSING"
        elif fact["declared_state"] == "unknown":
            code = "V1_ENVELOPE_FACT_UNKNOWN"
        elif fact["declared_value"] != fact["required_value"]:
            code = "V1_ENVELOPE_OUTSIDE"
        else:
            code = None
        if code is not None:
            expected_unresolved.append(
                {
                    "status": "APPLICABILITY_UNRESOLVED",
                    "code": code,
                    "fact_id": fact["fact_id"],
                    "overlay_kind": None,
                }
            )
    if overlay is not None:
        for kind in ("institutional", "funder"):
            if overlay[kind] == "not_provided":
                expected_unresolved.append(
                    {
                        "status": "APPLICABILITY_UNRESOLVED",
                        "code": "OVERLAY_SELECTION_NOT_PROVIDED",
                        "fact_id": None,
                        "overlay_kind": kind,
                    }
                )
    expected_unresolved.sort(
        key=lambda row: (
            row["code"],
            row["fact_id"] or "",
            row["overlay_kind"] or "",
        )
    )
    if _canonical_bytes(unresolved) != _canonical_bytes(expected_unresolved):
        _fail(
            "manifest.unresolved_reasons",
            "does not exactly match authority, envelope, and overlay states",
        )

    if not gate_permitted or envelope["state"] != "within_v1":
        if entries or excluded or observations:
            _fail(
                "manifest",
                "a closed authority or capability gate must have no entries, exclusions, or packet observations",
            )
    expected_readiness = _readiness(unresolved, entries)
    if administrative["submission_readiness"] != expected_readiness:
        _fail(
            "manifest.administrative_status.submission_readiness",
            "does not match unresolved and packet-owned readiness effects",
        )

    if root["boundary_footer"] != BOUNDARY_FOOTER:
        _fail("manifest.boundary_footer", "has changed")


def validate_submission_packet_manifest(
    manifest: dict[str, Any],
    inventory: dict[str, Any],
    packet_root: Path | str,
    *,
    context: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    resolved: dict[str, Any] | None = None,
) -> None:
    """Validate self-digests and exact deterministic replay from all named inputs."""
    supplied = (context is not None, registry is not None, resolved is not None)
    if any(supplied) and not all(supplied):
        raise ContractError("context, registry, and resolved authority inputs are all-or-none")
    if all(supplied):
        assert context is not None and registry is not None and resolved is not None
        validate_resolved_context(resolved, context, registry)
    _validate_manifest_shape(manifest)
    expected = build_submission_packet_manifest(
        inventory,
        packet_root,
        context=context,
        registry=registry,
        resolved=resolved,
    )
    if _canonical_bytes(manifest) != _canonical_bytes(expected):
        _fail(
            "manifest",
            "does not exactly match deterministic replay from the named inputs",
        )


def _md(value: Any) -> str:
    if value is None:
        return "not provided"
    if isinstance(value, bool):
        return "true" if value else "false"
    # Encode every ASCII punctuation mark as an entity. Markdown parses the
    # entity as text before browsers decode its visible character, so an
    # inventory path cannot create a link, image, HTML tag, code span, fence,
    # table delimiter, or extension-specific attribute syntax.
    return "".join(
        f"&#{ord(character)};"
        if (
            character.isascii()
            and not character.isalnum()
            and not character.isspace()
        )
        or unicodedata.category(character) in {"Zl", "Zp"}
        else character
        for character in str(value)
    )


def render_submission_packet_manifest(manifest: dict[str, Any]) -> str:
    """Render a shape- and self-digest-validated trusted manifest carrier."""
    _validate_manifest_shape(manifest)
    administrative = manifest["administrative_status"]
    authorization = administrative["authorization_status"]
    lines = [
        "# Human-Subjects Submission-Packet Manifest",
        "",
        "## Human-Subjects Administrative Status",
        "",
        f"Review pathway: {administrative['review_pathway']}",
        f"Submission readiness: {administrative['submission_readiness']}",
        f"Authorization status: {authorization['value']}",
        f"Review timeline: {administrative['review_timeline']}",
        f"Authorization source reference: {_md(authorization['source_reference'])}",
        f"Authorization provenance: {_md(authorization['provenance'])}",
        "",
        "Readiness and caller-supplied authorization are independent. This manifest does not derive or update authorization.",
        "",
        "## Packet Observations",
        "",
        "| Artifact | Relative path | State | Status | Reason codes |",
        "|---|---|---|---|---|",
    ]
    if manifest["packet_observations"]:
        for observation in manifest["packet_observations"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(observation["artifact_id"]),
                        _md(observation["relative_path"]),
                        _md(observation["state"]),
                        _md(observation["status"]),
                        _md(", ".join(observation["reason_codes"])),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none | none | none | none | none |")

    lines.extend(
        [
        "",
        "## Mechanical Evidence Entries",
        "",
        "| Requirement | Evidence | Responsibility | Status | Readiness effect | Matched artifact IDs | Reason codes |",
        "|---|---|---|---|---|---|---|",
        ]
    )
    if manifest["entries"]:
        for entry in manifest["entries"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(entry["requirement_ref"]["requirement_id"]),
                        _md(entry["evidence_ref"]["evidence_id"]),
                        _md(entry["responsibility"]),
                        _md(entry["status"]),
                        _md(entry["readiness_effect"]),
                        _md(", ".join(entry["matched_artifact_ids"]) or "none"),
                        _md(", ".join(entry["reason_codes"])),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none | none | none | none | none | none | none |")

    lines.extend(
        [
            "",
            "## Excluded Requirements",
            "",
            "| Requirement | Requirement pointer | Exclusion basis |",
            "|---|---|---|",
        ]
    )
    if manifest["excluded_requirements"]:
        for excluded in manifest["excluded_requirements"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(excluded["requirement_ref"]["requirement_id"]),
                        _md(excluded["requirement_ref"]["requirement_pointer"]),
                        _md(excluded["exclusion_basis"]),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none | none | none |")

    lines.extend(
        [
            "",
            "## Unresolved States",
            "",
            "| Status | Code | Fact ID | Overlay kind |",
            "|---|---|---|---|",
        ]
    )
    if manifest["unresolved_reasons"]:
        for reason in manifest["unresolved_reasons"]:
            lines.append(
                "| "
                + " | ".join(
                    _md(reason[field])
                    for field in ("status", "code", "fact_id", "overlay_kind")
                )
                + " |"
            )
    else:
        lines.append("| none | none | none | none |")

    lines.extend(
        [
            "",
            "## Institutional Acceptance Boundary",
            "",
            "| Status | Reason | Affects submission readiness |",
            "|---|---|---|",
            "| "
            + " | ".join(
                [
                    _md(manifest["acceptance_boundary"]["status"]),
                    _md(manifest["acceptance_boundary"]["reason_code"]),
                    _md(
                        manifest["acceptance_boundary"][
                            "affects_submission_readiness"
                        ]
                    ),
                ]
            )
            + " |",
            "",
            "> **Human-subjects boundary:** This output does not authorize recruitment, consent, access to identifiable data, intervention, or data collection.",
            "",
        ]
    )
    return "\n".join(lines)


def _add_authority_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--context", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--resolved", type=Path)


def _load_authority_arguments(
    args: argparse.Namespace,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    paths = (args.context, args.registry, args.resolved)
    if any(path is not None for path in paths) and not all(
        path is not None for path in paths
    ):
        raise ContractError("--context, --registry, and --resolved are all-or-none")
    if not all(path is not None for path in paths):
        return None, None, None
    return load_json(args.context), load_json(args.registry), load_json(args.resolved)


def _emit(text: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(text)
    else:
        output.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", allow_abbrev=False)
    build_parser.add_argument("--inventory", type=Path, required=True)
    build_parser.add_argument("--packet-root", type=Path, required=True)
    build_parser.add_argument("--output", type=Path)
    _add_authority_arguments(build_parser)

    validate_parser = subparsers.add_parser("validate", allow_abbrev=False)
    validate_parser.add_argument("--manifest", type=Path, required=True)
    validate_parser.add_argument("--inventory", type=Path, required=True)
    validate_parser.add_argument("--packet-root", type=Path, required=True)
    _add_authority_arguments(validate_parser)

    render_parser = subparsers.add_parser("render", allow_abbrev=False)
    render_parser.add_argument("--manifest", type=Path, required=True)
    render_parser.add_argument("--inventory", type=Path, required=True)
    render_parser.add_argument("--packet-root", type=Path, required=True)
    render_parser.add_argument("--output", type=Path)
    _add_authority_arguments(render_parser)

    args = parser.parse_args(argv)
    try:
        context, registry, resolved = _load_authority_arguments(args)
        inventory = load_json(args.inventory)
        if args.command == "build":
            manifest = build_submission_packet_manifest(
                inventory,
                args.packet_root,
                context=context,
                registry=registry,
                resolved=resolved,
            )
            # Compact canonical output stays within the same 8 MiB limit used
            # by the strict JSON loader, preserving build -> validate/render
            # round trips even at the exact boundary.
            _emit(_canonical_bytes(manifest).decode("utf-8"), args.output)
            return 0

        manifest = load_json(args.manifest)
        validate_submission_packet_manifest(
            manifest,
            inventory,
            args.packet_root,
            context=context,
            registry=registry,
            resolved=resolved,
        )
        if args.command == "validate":
            print("Submission-packet manifest validation passed (#667).")
            return 0
        _emit(render_submission_packet_manifest(manifest), args.output)
        return 0
    except (ContractError, OSError, ValueError, RecursionError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
