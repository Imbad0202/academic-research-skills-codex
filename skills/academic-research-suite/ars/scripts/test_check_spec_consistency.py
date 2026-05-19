from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_spec_consistency.py")
SPEC = importlib.util.spec_from_file_location("check_spec_consistency", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
check_spec_consistency = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_spec_consistency)


def configure_codex_root(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "suite" / "ars"
    root.mkdir(parents=True)
    (root.parent / "manifest.json").write_text(
        json.dumps(
            {
                "generated_for": "codex",
                "excluded_patterns": ["examples/showcase/*.pdf"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(check_spec_consistency, "ROOT", root)
    check_spec_consistency.ERRORS.clear()
    return root


def test_check_claude_md_skips_when_file_missing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(check_spec_consistency, "ROOT", tmp_path)
    check_spec_consistency.ERRORS.clear()

    check_spec_consistency.check_claude_md()

    assert check_spec_consistency.ERRORS == []
    assert (
        "Skipping .claude/CLAUDE.md checks: file not present in this distribution."
        in capsys.readouterr().out
    )


def test_relative_markdown_links_skip_codex_excluded_patterns(
    tmp_path: Path, monkeypatch
) -> None:
    root = configure_codex_root(tmp_path, monkeypatch)
    (root / "README.md").write_text(
        "[Final Paper](examples/showcase/full_paper_apa7.pdf)\n",
        encoding="utf-8",
    )

    check_spec_consistency.check_relative_markdown_links("README.md")

    assert check_spec_consistency.ERRORS == []


def test_relative_markdown_links_report_unexcluded_missing_targets(
    tmp_path: Path, monkeypatch
) -> None:
    root = configure_codex_root(tmp_path, monkeypatch)
    (root / "README.md").write_text(
        "[Missing](docs/missing.md)\n",
        encoding="utf-8",
    )

    check_spec_consistency.check_relative_markdown_links("README.md")

    assert check_spec_consistency.ERRORS == [
        "README.md: broken relative markdown link 'docs/missing.md'"
    ]


def test_check_setup_docs_accepts_codex_overlay_text(
    tmp_path: Path, monkeypatch
) -> None:
    root = configure_codex_root(tmp_path, monkeypatch)
    (root / "docs").mkdir()
    (root / "docs" / "SETUP.md").write_text(
        "Direct `.docx` generation uses Pandoc.\n"
        "PDF output requires `tectonic` and the relevant fonts.\n",
        encoding="utf-8",
    )
    (root / "docs" / "SETUP.zh-TW.md").write_text(
        "直接產生 `.docx` 需要 Pandoc。\n"
        "PDF 輸出需要 `tectonic` 與相關字型。\n",
        encoding="utf-8",
    )

    check_spec_consistency.check_setup_docs()

    assert check_spec_consistency.ERRORS == []
