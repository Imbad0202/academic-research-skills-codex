#!/usr/bin/env python3
"""Lint: version labels stay aligned across .claude/CLAUDE.md, SKILL.md frontmatter, and CHANGELOG.md.

Invariants enforced:
  1. Every skill listed in .claude/CLAUDE.md Skills Overview table has a version
     equal to its own SKILL.md metadata.version.
  2. .claude/CLAUDE.md "**Suite version**: X.Y.Z" equals the most recent
     "## [X.Y.Z]" entry in CHANGELOG.md.
  3. academic-pipeline version in the table equals the suite version (pipeline
     = orchestrator, by convention tracks the suite release).

Runs from repo root by default; `--path` lets tests point at a fake tree.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _skill_lint import parse_frontmatter, FrontmatterError


TABLE_ROW_RE = re.compile(r"^\|\s*`([a-z0-9-]+)`\s+v(\d+\.\d+\.\d+)\s*\|", re.MULTILINE)
SUITE_VERSION_RE = re.compile(
    r"^\s*-\s*\*\*Suite version\*\*:\s*(\d+\.\d+\.\d+)", re.MULTILINE
)
CHANGELOG_ENTRY_RE = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]", re.MULTILINE)

PIPELINE_SKILL_NAME = "academic-pipeline"


def _parse_table_versions(claude_md_text: str) -> dict[str, str]:
    """Return mapping skill_name -> version from the Skills Overview table."""
    return dict(TABLE_ROW_RE.findall(claude_md_text))


def _parse_suite_version(claude_md_text: str) -> str | None:
    m = SUITE_VERSION_RE.search(claude_md_text)
    return m.group(1) if m else None


def _parse_changelog_latest(changelog_text: str) -> str | None:
    m = CHANGELOG_ENTRY_RE.search(changelog_text)
    return m.group(1) if m else None


def _find_codex_adapter_root(root: Path) -> Path | None:
    candidates = [root, root.parent]
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file() and (candidate / "manifest.json").is_file():
            return candidate
    return None


def _read_version_file(adapter_root: Path, manifest: dict) -> str | None:
    version_file = manifest.get("version_file") or "VERSION"
    candidates = [adapter_root, *adapter_root.parents]
    for base in candidates:
        candidate = base / version_file
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return None


def _check_codex_adapter(root: Path) -> list[str]:
    adapter_root = _find_codex_adapter_root(root)
    if adapter_root is None:
        return [f"{root / '.claude' / 'CLAUDE.md'}: not found"]

    errors: list[str] = []
    manifest_path = adapter_root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{manifest_path}: malformed JSON: {exc}"]

    if manifest.get("generated_for") != "codex":
        return [f"{root / '.claude' / 'CLAUDE.md'}: not found"]

    skill_path = adapter_root / "SKILL.md"
    try:
        fm = parse_frontmatter(skill_path)
    except FrontmatterError as exc:
        return [str(exc)]
    metadata = (fm or {}).get("metadata") or {}
    skill_version = metadata.get("version")
    manifest_version = manifest.get("adapter_version")
    version_file_value = _read_version_file(adapter_root, manifest)

    if skill_version != manifest_version:
        errors.append(
            f"{skill_path}: metadata.version {skill_version!r} does not match "
            f"{manifest_path}: adapter_version {manifest_version!r}"
        )
    if version_file_value is None:
        errors.append(
            f"{manifest_path}: version_file {manifest.get('version_file', 'VERSION')!r} not found"
        )
    elif skill_version != version_file_value:
        errors.append(
            f"{skill_path}: metadata.version {skill_version!r} does not match "
            f"VERSION {version_file_value!r}"
        )
    return errors


def check(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    claude_md = root / ".claude" / "CLAUDE.md"
    if not claude_md.is_file():
        return _check_codex_adapter(root)
    claude_text = claude_md.read_text(encoding="utf-8")

    table_versions = _parse_table_versions(claude_text)
    if not table_versions:
        errors.append(
            f"{claude_md}: Skills Overview table has no parseable "
            "`<skill>` vX.Y.Z rows"
        )

    suite_version = _parse_suite_version(claude_text)
    if suite_version is None:
        errors.append(
            f"{claude_md}: missing '**Suite version**: X.Y.Z' line"
        )

    changelog = root / "CHANGELOG.md"
    if not changelog.is_file():
        errors.append(f"{changelog}: not found")
    else:
        latest = _parse_changelog_latest(changelog.read_text(encoding="utf-8"))
        if latest is None:
            errors.append(f"{changelog}: no '## [X.Y.Z]' entry found")
        elif suite_version is not None and latest != suite_version:
            errors.append(
                f"{claude_md}: Suite version {suite_version!r} does not match "
                f"CHANGELOG latest entry {latest!r}"
            )

    for skill_name, table_version in sorted(table_versions.items()):
        skill_md = root / skill_name / "SKILL.md"
        if not skill_md.is_file():
            errors.append(
                f"{claude_md}: table lists {skill_name!r} v{table_version} "
                f"but {skill_md} does not exist"
            )
            continue
        try:
            fm = parse_frontmatter(skill_md)
        except FrontmatterError as exc:
            errors.append(str(exc))
            continue
        if fm is None:
            errors.append(f"{skill_md}: missing YAML frontmatter")
            continue
        metadata = fm.get("metadata") or {}
        declared = metadata.get("version")
        if declared is None:
            errors.append(f"{skill_md}: metadata.version is missing")
            continue
        declared_str = str(declared)
        if declared_str != table_version:
            errors.append(
                f"{claude_md}: {skill_name!r} listed as v{table_version} but "
                f"{skill_md} metadata.version is {declared_str!r}"
            )

    if suite_version is not None:
        pipeline_in_table = table_versions.get(PIPELINE_SKILL_NAME)
        if pipeline_in_table is not None and pipeline_in_table != suite_version:
            errors.append(
                f"{claude_md}: {PIPELINE_SKILL_NAME} listed as "
                f"v{pipeline_in_table} but suite version is {suite_version!r} "
                "(pipeline tracks the suite release)"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()

    errors = check(args.path)
    if errors:
        print("Version consistency check failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Version consistency check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
