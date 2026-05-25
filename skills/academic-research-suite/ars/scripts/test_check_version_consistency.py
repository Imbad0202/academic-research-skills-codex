"""Unit tests for check_version_consistency.py."""
from __future__ import annotations

import subprocess
import textwrap
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts._test_helpers import run_script

SCRIPT = Path(__file__).resolve().parent / "check_version_consistency.py"


def _run(root: Path) -> subprocess.CompletedProcess:
    return run_script(SCRIPT, "--path", str(root))


def _write_skill(root: Path, name: str, version: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        textwrap.dedent(
            f"""\
            ---
            name: {name}
            description: "fixture"
            metadata:
              version: "{version}"
              last_updated: "2026-04-22"
              status: active
              data_access_level: raw
              task_type: open-ended
            ---

            # {name}
            """
        ),
        encoding="utf-8",
    )


def _write_claude_md(
    root: Path,
    suite_version: str,
    table_rows: list[tuple[str, str]],
) -> None:
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| `{name}` v{ver} | purpose | modes |" for name, ver in table_rows
    )
    text = (
        "# Academic Research Skills\n"
        "\n"
        "## Skills Overview\n"
        "\n"
        "| Skill | Purpose | Key Modes |\n"
        "|-------|---------|-----------|\n"
        f"{rows}\n"
        "\n"
        "## Version Info\n"
        f"- **Suite version**: {suite_version} (per CHANGELOG.md)\n"
    )
    (claude_dir / "CLAUDE.md").write_text(text, encoding="utf-8")


def _write_changelog(root: Path, latest_version: str) -> None:
    (root / "CHANGELOG.md").write_text(
        textwrap.dedent(
            f"""\
            # Changelog

            ## [{latest_version}] - 2026-04-22

            ### Added
            - fixture entry
            """
        ),
        encoding="utf-8",
    )


def _write_codex_fixture(root: Path, version: str = "0.1.8", manifest_version: str | None = None) -> Path:
    package_root = root / "skills" / "academic-research-suite"
    ars_root = package_root / "ars"
    ars_root.mkdir(parents=True)
    (root / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    (package_root / "manifest.json").write_text(
        json.dumps({
            "name": "academic-research-suite",
            "adapter_version": manifest_version or version,
            "version_file": "VERSION",
            "generated_for": "codex",
        }),
        encoding="utf-8",
    )
    (package_root / "SKILL.md").write_text(
        textwrap.dedent(
            f"""\
            ---
            name: academic-research-suite
            description: "fixture"
            metadata:
              version: "{version}"
              codex_adapter: true
            ---

            # Academic Research Suite
            """
        ),
        encoding="utf-8",
    )
    return ars_root


def _write_aligned_fixture(root: Path) -> None:
    """Everything lines up — baseline for PASS cases and drift mutations."""
    skills = [
        ("deep-research", "2.9.0"),
        ("academic-paper", "3.1.0"),
        ("academic-paper-reviewer", "1.8.1"),
        ("academic-pipeline", "3.5.0"),
    ]
    for name, ver in skills:
        _write_skill(root, name, ver)
    _write_claude_md(root, suite_version="3.5.0", table_rows=skills)
    _write_changelog(root, latest_version="3.5.0")


def _write_aligned_fixture_v351(root: Path) -> None:
    """v3.5.1 suite: deep-research 2.9.1, academic-pipeline 3.5.1."""
    skills = [
        ("deep-research", "2.9.1"),
        ("academic-paper", "3.1.0"),
        ("academic-paper-reviewer", "1.8.1"),
        ("academic-pipeline", "3.5.1"),
    ]
    for name, ver in skills:
        _write_skill(root, name, ver)
    _write_claude_md(root, suite_version="3.5.1", table_rows=skills)
    _write_changelog(root, latest_version="3.5.1")


class TestVersionConsistency(unittest.TestCase):
    def test_all_aligned_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            result = _run(root)
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )

    def test_all_aligned_v351_passes(self) -> None:
        """v3.5.1 suite (deep-research 2.9.1, academic-pipeline 3.5.1) must pass."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture_v351(root)
            result = _run(root)
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )

    def test_table_version_drift_fails(self) -> None:
        """Table lists deep-research v2.9.0 but SKILL.md says 2.8.0 — must fail."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            _write_skill(root, "deep-research", "2.8.0")
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("deep-research", result.stdout)
            self.assertIn("2.9.0", result.stdout)
            self.assertIn("2.8.0", result.stdout)

    def test_suite_version_vs_changelog_drift_fails(self) -> None:
        """CLAUDE.md suite version != CHANGELOG latest entry — must fail."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            _write_changelog(root, latest_version="3.4.0")
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("3.5.0", result.stdout)
            self.assertIn("3.4.0", result.stdout)
            self.assertIn("CHANGELOG", result.stdout)

    def test_pipeline_version_vs_suite_drift_fails(self) -> None:
        """academic-pipeline version in table must equal suite version."""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            # Drop pipeline to 3.4.0 in both table and SKILL.md, keep suite at 3.5.0.
            # This isolates invariant 3 (pipeline tracks suite) from invariant 1
            # (SKILL.md == table).
            _write_skill(root, "academic-pipeline", "3.4.0")
            _write_claude_md(
                root,
                suite_version="3.5.0",
                table_rows=[
                    ("deep-research", "2.9.0"),
                    ("academic-paper", "3.1.0"),
                    ("academic-paper-reviewer", "1.8.1"),
                    ("academic-pipeline", "3.4.0"),
                ],
            )
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("academic-pipeline", result.stdout)

    def test_skill_missing_frontmatter_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            (root / "deep-research" / "SKILL.md").write_text(
                "# deep-research\n\nNo frontmatter here.\n",
                encoding="utf-8",
            )
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("deep-research", result.stdout)

    def test_skill_listed_in_table_but_missing_on_disk_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            import shutil
            shutil.rmtree(root / "academic-paper-reviewer")
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("academic-paper-reviewer", result.stdout)

    def test_missing_suite_version_in_claude_md_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_aligned_fixture(root)
            (root / ".claude" / "CLAUDE.md").write_text(
                textwrap.dedent(
                    """\
                    # Academic Research Skills

                    ## Skills Overview

                    | Skill | Purpose | Key Modes |
                    |-------|---------|-----------|
                    | `deep-research` v2.9.0 | x | y |
                    | `academic-paper` v3.1.0 | x | y |
                    | `academic-paper-reviewer` v1.8.1 | x | y |
                    | `academic-pipeline` v3.5.0 | x | y |

                    ## Version Info
                    - No suite version line here.
                    """
                ),
                encoding="utf-8",
            )
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Suite version", result.stdout)

    def test_codex_adapter_without_claude_md_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            ars_root = _write_codex_fixture(root)
            result = _run(ars_root)
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
            )

    def test_codex_adapter_manifest_version_drift_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            ars_root = _write_codex_fixture(root, manifest_version="0.1.7")
            result = _run(ars_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("adapter_version", result.stdout)


if __name__ == "__main__":
    unittest.main()
