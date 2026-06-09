#!/usr/bin/env python3
"""Validate a Material Passport YAML's `repro_lock` sub-block.

Usage: python scripts/check_repro_lock.py path/to/passport.yaml

- Missing `repro_lock` key (not even null): ERROR, exit 1.
- `repro_lock: null`: WARN, exit 0 (honest opt-out).
- Populated block with all required sub-fields: OK, exit 0.
- Populated block with missing sub-field or unknown schema_version: ERROR, exit 1.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
SUPPORTED_HASH_TIMINGS = {"skill-load"}

REQUIRED_FIELDS = {
    "schema_version",
    "stochasticity_declaration",
    "ars_version",
    "model",
    "prompts",
    "materials",
    "external_protocols",
    "cross_model",
}

REQUIRED_MODEL = {"family", "id", "weight_stable"}
REQUIRED_PROMPTS = {"hash_timing", "skill_md_hash", "agents_bundle_hash"}
REQUIRED_MATERIALS = {"list_hash", "count"}
REQUIRED_EXTERNAL = {"s2_api_protocol_version", "s2_snapshot_available"}
REQUIRED_CROSSMODEL = {"enabled", "secondary_model_id"}


def validate_block(lock: dict) -> list[str]:
    errors = []

    missing = REQUIRED_FIELDS - set(lock.keys())
    for m in sorted(missing):
        errors.append(f"repro_lock: missing required field '{m}'")

    sv = lock.get("schema_version")
    if sv is not None and sv not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"repro_lock.schema_version = {sv!r}, must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )

    for name, required, sub in [
        ("model", REQUIRED_MODEL, lock.get("model")),
        ("prompts", REQUIRED_PROMPTS, lock.get("prompts")),
        ("materials", REQUIRED_MATERIALS, lock.get("materials")),
        ("external_protocols", REQUIRED_EXTERNAL, lock.get("external_protocols")),
        ("cross_model", REQUIRED_CROSSMODEL, lock.get("cross_model")),
    ]:
        if sub is None:
            continue  # missing top-level already reported
        if not isinstance(sub, dict):
            errors.append(f"repro_lock.{name} must be a mapping")
            continue
        for m in sorted(required - set(sub.keys())):
            errors.append(f"repro_lock.{name}: missing required field '{m}'")

    prompts = lock.get("prompts")
    if isinstance(prompts, dict):
        ht = prompts.get("hash_timing")
        if ht is not None and ht not in SUPPORTED_HASH_TIMINGS:
            errors.append(
                f"repro_lock.prompts.hash_timing = {ht!r}, "
                f"must be one of {sorted(SUPPORTED_HASH_TIMINGS)} (see shared/artifact_reproducibility_pattern.md)"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("passport", type=Path)
    args = parser.parse_args()

    try:
        doc = yaml.safe_load(args.passport.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: failed to load {args.passport}: {exc}")
        return 1

    if not isinstance(doc, dict):
        print(f"ERROR: {args.passport}: top-level must be a mapping")
        return 1

    if "repro_lock" not in doc:
        print("ERROR: repro_lock key is missing. Set 'repro_lock: null' to opt out explicitly.")
        return 1

    lock = doc["repro_lock"]
    if lock is None:
        print("WARN: repro_lock is null — honest opt-out. Reproducibility reduced.", file=sys.stderr)
        print("OK (with WARN): passport valid; repro_lock explicitly null — see stderr.", flush=True)
        return 0

    if not isinstance(lock, dict):
        print(f"ERROR: repro_lock must be null or a mapping, got {type(lock).__name__}")
        return 1

    errors = validate_block(lock)
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(
            f"\n{len(errors)} violation(s). "
            f"See shared/artifact_reproducibility_pattern.md for required fields.",
            file=sys.stderr,
        )
        return 1

    print("OK: passport repro_lock is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
