#!/usr/bin/env python3
"""Check the static #667 submission-packet contract and consumer wiring."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


INVENTORY_SCHEMA = Path("shared/contracts/human_subjects/submission_packet_inventory.schema.json")
MANIFEST_SCHEMA = Path("shared/contracts/human_subjects/submission_packet_manifest.schema.json")
REGISTRY = Path("shared/human_subjects_authority_registry.json")
RUNTIME = Path("scripts/build_submission_packet_manifest.py")
CONTRACT_README = Path("shared/contracts/README.md")
AUTHORITY_PROTOCOL = Path("shared/references/human_subjects_authority_protocol.md")
PACKET_PROTOCOL = Path("shared/references/submission_packet_manifest_protocol.md")
DESIGN_SPEC = Path("docs/design/2026-08-09-667-submission-packet-manifest-spec.md")
DEEP_SKILL = Path("deep-research/WORKFLOW.md")
ETHICS_AGENT = Path("deep-research/agents/ethics_review_agent.md")
ARCHITECT = Path("deep-research/agents/research_architect_agent.md")
ARCHITECT_MIRROR = Path("agents/research_architect_agent.md")

FOOTER = (
    "Human-subjects boundary: This output does not authorize recruitment, "
    "consent, access to identifiable data, intervention, or data collection."
)
STATUSES = {
    "DOCUMENTED",
    "NOT_LOCATED",
    "CONFLICTING",
    "APPLICABILITY_UNRESOLVED",
    "ACCEPTANCE_UNVERIFIED",
}
ENVELOPE_FACTS = {
    "packet_v1.non_clinical": True,
    "packet_v1.single_institution": True,
    "packet_v1.competent_adults_only": True,
    "packet_v1.biospecimens_involved": False,
    "packet_v1.regulated_clinical_trial": False,
    "packet_v1.cross_border_material_transfer": False,
    "packet_v1.multisite_reliance": False,
}
FORBIDDEN_OUTPUT_KEYS = {
    "verdict",
    "review_level",
    "approval",
    "approval_status",
    "clearance",
    "compliance",
    "conformance",
    "adequacy",
    "content_adequacy",
    "content_coverage",
    "language_quality",
    "quality_score",
    "authorization_decision",
    "institutional_acceptance",
    "waiver_granted",
    "exception_granted",
    "excerpt",
    "quote",
    "description",
    "summary",
    "text",
    "content",
    "structured_expectations",
}
FORBIDDEN_IMPORT_ROOTS = {"http", "requests", "socket", "subprocess", "urllib"}
FORBIDDEN_SCAN_CALLS = {
    "glob",
    "iglob",
    "rglob",
    "iterdir",
    "listdir",
    "scandir",
    "walk",
    "fwalk",
}
FORBIDDEN_REGISTRY_READS = {"description", "structured_expectations"}
REPLAY_CONTRACT_SNIPPETS = {
    PACKET_PROTOCOL: (
        "Before accepting or rendering a serialized manifest, call\n"
        "`validate_submission_packet_manifest`"
    ),
    ETHICS_AGENT: (
        "replay-validated with `validate_submission_packet_manifest("
        "manifest, inventory, packet_root,"
    ),
    ARCHITECT: (
        "confirms a successful `validate_submission_packet_manifest(...)` replay"
    ),
}


class DuplicateKeyError(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicates,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite value: {token}")
        ),
    )
    if not isinstance(value, dict):
        raise ValueError("top level must be an object")
    return value


def _schema_property_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for child in value.values():
            names.update(_schema_property_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_schema_property_names(child))
    return names


def _constant_key(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _runtime_ast_errors(source: str) -> list[str]:
    errors: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"{RUNTIME}: cannot parse: {exc}"]

    functions = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_functions = {
        "validate_submission_packet_inventory",
        "observe_submission_packet",
        "build_submission_packet_manifest",
        "validate_submission_packet_manifest",
        "render_submission_packet_manifest",
        "main",
    }
    for name in sorted(required_functions - functions):
        errors.append(f"{RUNTIME}: missing public #667 function {name}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                    errors.append(f"{RUNTIME}: forbidden transport/process import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                errors.append(f"{RUNTIME}: forbidden transport/process import {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_SCAN_CALLS:
                errors.append(f"{RUNTIME}: forbidden ambient filesystem scan call {node.func.attr}()")
            elif isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_SCAN_CALLS:
                errors.append(f"{RUNTIME}: forbidden ambient filesystem scan call {node.func.id}()")
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"get", "pop", "setdefault"}
                and node.args
                and _constant_key(node.args[0]) in FORBIDDEN_REGISTRY_READS
            ):
                errors.append(
                    f"{RUNTIME}: deterministic layer reads forbidden registry content field "
                    f"{_constant_key(node.args[0])!r}"
                )
        elif isinstance(node, ast.Subscript):
            key = _constant_key(node.slice)
            if key in FORBIDDEN_REGISTRY_READS:
                errors.append(
                    f"{RUNTIME}: deterministic layer reads forbidden registry content field {key!r}"
                )
    return errors


def run_checks(root: Path) -> list[str]:
    errors: list[str] = []
    json_values: dict[Path, dict[str, Any]] = {}
    texts: dict[Path, str] = {}

    for rel in (INVENTORY_SCHEMA, MANIFEST_SCHEMA, REGISTRY):
        try:
            json_values[rel] = _load_json(root / rel)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{rel}: cannot read strict JSON: {exc}")
    for rel in (
        RUNTIME,
        CONTRACT_README,
        AUTHORITY_PROTOCOL,
        PACKET_PROTOCOL,
        DESIGN_SPEC,
        DEEP_SKILL,
        ETHICS_AGENT,
        ARCHITECT,
        ARCHITECT_MIRROR,
    ):
        try:
            texts[rel] = (root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{rel}: cannot read: {exc}")

    inventory_schema = json_values.get(INVENTORY_SCHEMA)
    if inventory_schema is not None:
        const = inventory_schema.get("properties", {}).get("schema_version", {}).get("const")
        if const != "submission-packet-inventory/1.0":
            errors.append(f"{INVENTORY_SCHEMA}: wrong schema_version const")

    manifest_schema = json_values.get(MANIFEST_SCHEMA)
    if manifest_schema is not None:
        const = manifest_schema.get("properties", {}).get("schema_version", {}).get("const")
        if const != "submission-packet-manifest/1.0":
            errors.append(f"{MANIFEST_SCHEMA}: wrong schema_version const")
        status_enum = (
            manifest_schema.get("$defs", {})
            .get("entry", {})
            .get("properties", {})
            .get("status", {})
            .get("enum")
        )
        if set(status_enum or []) != STATUSES:
            errors.append(f"{MANIFEST_SCHEMA}: five-word deterministic status vocabulary drifted")
        footer = manifest_schema.get("properties", {}).get("boundary_footer", {}).get("const")
        if footer != FOOTER:
            errors.append(f"{MANIFEST_SCHEMA}: fixed #665 boundary footer drifted")
        forbidden = _schema_property_names(manifest_schema) & FORBIDDEN_OUTPUT_KEYS
        if forbidden:
            errors.append(
                f"{MANIFEST_SCHEMA}: determination/content keys are representable: "
                f"{', '.join(sorted(forbidden))}"
            )

    registry = json_values.get(REGISTRY)
    if registry is not None:
        definitions = {
            row.get("fact_id"): row
            for row in registry.get("fact_definitions", [])
            if isinstance(row, dict)
        }
        for fact_id in ENVELOPE_FACTS:
            row = definitions.get(fact_id)
            if row is None:
                errors.append(f"{REGISTRY}: missing #667 envelope fact {fact_id}")
                continue
            if row.get("value_type") != "boolean" or row.get("allowed_values") is not None:
                errors.append(f"{REGISTRY}: {fact_id} must remain an open boolean declaration")
            description = row.get("description")
            if not isinstance(description, str) or "not a legal or institutional characterization" not in description:
                errors.append(f"{REGISTRY}: {fact_id} lost its non-characterization boundary")
        authority_rows = json.dumps(
            {"profiles": registry.get("profiles"), "overlays": registry.get("overlays")},
            ensure_ascii=False,
            sort_keys=True,
        )
        for fact_id in ENVELOPE_FACTS:
            if fact_id in authority_rows:
                errors.append(f"{REGISTRY}: capability fact {fact_id} entered authority applicability")

    required_tokens: dict[Path, tuple[str, ...]] = {
        CONTRACT_README: (
            "shared/contracts/human_subjects/submission_packet_inventory.schema.json",
            "shared/contracts/human_subjects/submission_packet_manifest.schema.json",
        ),
        AUTHORITY_PROTOCOL: (
            "shared/references/submission_packet_manifest_protocol.md",
            "structured_expectations",
            *ENVELOPE_FACTS.keys(),
        ),
        PACKET_PROTOCOL: (
            "validate_submission_packet_manifest",
            "structured_expectations",
            "ACCEPTANCE_UNVERIFIED",
            FOOTER,
        ),
        DESIGN_SPEC: (
            "submission-packet-inventory/1.0",
            "submission-packet-manifest/1.0",
            "structured_expectations",
        ),
        DEEP_SKILL: (
            "shared/references/submission_packet_manifest_protocol.md",
            "shared/contracts/human_subjects/submission_packet_manifest.schema.json",
        ),
        ETHICS_AGENT: (
            "validate_submission_packet_manifest",
            "shared/references/submission_packet_manifest_protocol.md",
            "shared/contracts/human_subjects/submission_packet_manifest.schema.json",
            "structured_expectations",
        ),
        ARCHITECT: (
            "validate_submission_packet_manifest",
            "shared/references/submission_packet_manifest_protocol.md",
            "shared/contracts/human_subjects/submission_packet_manifest.schema.json",
            "structured_expectations",
        ),
    }
    for rel, tokens in required_tokens.items():
        text = texts.get(rel)
        if text is None:
            continue
        for token in tokens:
            if token not in text:
                errors.append(f"{rel}: missing #667 contract pointer/text {token!r}")

    # Pin the primary #667 replay instruction in its owning paragraph. A later
    # downstream handoff may legitimately name the same function, but that
    # unscoped duplicate must not mask deletion of the normative instruction.
    for rel, snippet in REPLAY_CONTRACT_SNIPPETS.items():
        text = texts.get(rel)
        if text is not None and snippet not in text:
            errors.append(f"{rel}: missing primary #667 replay-contract instruction")

    architect = texts.get(ARCHITECT)
    mirror = texts.get(ARCHITECT_MIRROR)
    if architect is not None and mirror is not None and architect != mirror:
        errors.append(f"{ARCHITECT_MIRROR}: research-architect mirror drift")

    runtime = texts.get(RUNTIME)
    if runtime is not None:
        errors.extend(_runtime_ast_errors(runtime))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    errors = run_checks(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Submission-packet manifest integration check passed (#667).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
