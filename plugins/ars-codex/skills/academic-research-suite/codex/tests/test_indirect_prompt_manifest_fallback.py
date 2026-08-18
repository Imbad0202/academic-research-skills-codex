from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


SUITE_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = SUITE_ROOT / "ars" / "scripts" / "run_indirect_prompt_injection_no_call.py"
VALID_COMMIT = "2b639c12ee4e7c694a32336cc59dc2616e0d89fe"


def _load_runner():
    scripts_root = str(RUNNER_PATH.parent)
    sys.path.insert(0, scripts_root)
    try:
        spec = importlib.util.spec_from_file_location(
            "ars_codex_indirect_prompt_manifest_fallback", RUNNER_PATH
        )
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(scripts_root)


def _write_manifest(vendor_root: Path, payload: object) -> None:
    vendor_root.mkdir()
    (vendor_root.parent / "manifest.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_no_git_vendor_resolves_exact_manifest_source_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner()
    vendor_root = tmp_path / "ars"
    _write_manifest(
        vendor_root,
        {
            "source_repositories": [
                {"name": "academic-research-skills", "commit": VALID_COMMIT},
                {"name": "experiment-agent", "commit": "1" * 40},
            ]
        },
    )
    monkeypatch.setattr(runner, "REPO_ROOT", vendor_root)

    assert runner._repository_head_commit() == VALID_COMMIT


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"source_repositories": {}},
        {"source_repositories": []},
        {
            "source_repositories": [
                {"name": "academic-research-skills", "commit": "not-a-commit"}
            ]
        },
        {
            "source_repositories": [
                {"name": "academic-research-skills", "commit": VALID_COMMIT},
                {"name": "academic-research-skills", "commit": VALID_COMMIT},
            ]
        },
    ],
)
def test_no_git_vendor_manifest_shape_and_source_lock_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: object
) -> None:
    runner = _load_runner()
    vendor_root = tmp_path / "ars"
    _write_manifest(vendor_root, payload)
    monkeypatch.setattr(runner, "REPO_ROOT", vendor_root)

    with pytest.raises(
        runner.EnvelopeError,
        match="cannot resolve suite_commit from Codex package manifest",
    ):
        runner._repository_head_commit()


def test_no_git_vendor_manifest_duplicate_keys_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _load_runner()
    vendor_root = tmp_path / "ars"
    vendor_root.mkdir()
    (vendor_root.parent / "manifest.json").write_text(
        '{"source_repositories":[],"source_repositories":[]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "REPO_ROOT", vendor_root)

    with pytest.raises(runner.EnvelopeError, match="duplicate JSON key"):
        runner._repository_head_commit()
