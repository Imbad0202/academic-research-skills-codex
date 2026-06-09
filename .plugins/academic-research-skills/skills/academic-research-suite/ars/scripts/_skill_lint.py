"""Shared helpers for SKILL.md frontmatter linting.

Used by check_data_access_level.py and check_task_type.py to validate
that every top-level SKILL.md declares a required metadata field with
a value drawn from a closed vocabulary.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SKIP_DIRS = frozenset(
    {"shared", "scripts", "docs", ".git", ".github", "examples", ".local-plans", ".claude"}
)


class FrontmatterError(Exception):
    """Raised when SKILL.md frontmatter cannot be parsed.

    Distinct from a missing fence (returns None) and an empty fence
    (returns {}). Callers should catch this and surface the path +
    parser detail on stdout, not stderr — CI logs commonly capture
    only stdout.
    """


def codex_entry_name(root: Path) -> str:
    """Return WORKFLOW.md for the Codex vendored layout, otherwise SKILL.md."""
    manifest_path = root.parent / "manifest.json"
    if not manifest_path.is_file():
        return "SKILL.md"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "SKILL.md"
    if isinstance(manifest, dict) and manifest.get("generated_for") == "codex":
        return "WORKFLOW.md"
    return "SKILL.md"


def iter_skill_files(root: Path, entry_name: str = "SKILL.md") -> list[Path]:
    """Top-level entry files only. Skips SKIP_DIRS."""
    results: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS:
            continue
        skill_md = child / entry_name
        if skill_md.is_file():
            results.append(skill_md)
    return results


def parse_frontmatter(path: Path) -> dict | None:
    """Parse the YAML frontmatter of a SKILL.md.

    Three outcomes:
      - dict (possibly empty) — fence present and parseable
      - None                  — no opening '---' fence
      - raises FrontmatterError — fence present but YAML invalid
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    match = re.match(r"\A---\r?\n(?P<fm>.*?)(?:\r?\n)---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        raise FrontmatterError(f"{path}: missing closing YAML frontmatter fence")
    fm = match.group("fm")
    try:
        data = yaml.safe_load(fm) or {}
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"{path}: malformed YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontmatterError(
            f"{path}: YAML frontmatter must be a mapping/object, got {type(data).__name__}"
        )
    return data


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Split YAML frontmatter from body. Lenient variant of parse_frontmatter.

    Unlike parse_frontmatter, callers here need access to the body and
    prefer "no frontmatter" to an exception when YAML is malformed (the
    caller's surrounding check will surface the structural error). Both
    invalid-fence and invalid-YAML return (None, text) rather than raising.
    """
    if not text.startswith("---"):
        return None, text
    match = re.match(r"\A---\r?\n(?P<fm>.*?)(?:\r?\n)---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        return None, text
    try:
        data = yaml.safe_load(match.group("fm")) or {}
    except yaml.YAMLError:
        return None, text
    if not isinstance(data, dict):
        return None, text
    return data, text[match.end():]


def check_metadata_field(
    root: Path,
    field: str,
    legal_values: set[str] | frozenset[str],
    entry_name: str = "SKILL.md",
) -> list[str]:
    """Return a list of human-readable violation messages, empty if all pass."""
    violations: list[str] = []
    skills = iter_skill_files(root, entry_name=entry_name)
    if not skills:
        violations.append(f"no {entry_name} files found under {root}")
        return violations
    for path in skills:
        try:
            fm = parse_frontmatter(path)
        except FrontmatterError as exc:
            violations.append(str(exc))
            continue
        if fm is None:
            violations.append(f"{path}: missing YAML frontmatter")
            continue
        metadata = fm.get("metadata") or {}
        if field not in metadata:
            violations.append(f"{path}: metadata.{field} is missing")
            continue
        value = metadata[field]
        if value not in legal_values:
            violations.append(
                f"{path}: metadata.{field} = {value!r}, "
                f"must be one of {sorted(legal_values)}"
            )
    return violations


def run_lint(
    field: str,
    legal_values: set[str] | frozenset[str],
    ok_message: str,
    entry_name: str | None = None,
) -> int:
    """argparse + check + print + exit-code wrapper used by both check scripts."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()

    selected_entry = entry_name or codex_entry_name(args.path)
    violations = check_metadata_field(
        args.path, field, legal_values, entry_name=selected_entry
    )
    if violations:
        for v in violations:
            print(f"ERROR: {v}")
        print(f"\n{len(violations)} violation(s) found.", file=sys.stderr)
        return 1
    print(ok_message.replace("SKILL.md", selected_entry))
    return 0
