"""Tests for bootstrap_timeline_yaml.py (opt-in Crossref + pdftotext)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/bootstrap_timeline_yaml.py"


def test_bootstrap_dry_run_emits_skeleton(tmp_path):
    """Dry-run produces a timeline.yaml skeleton without calling Crossref/pdftotext."""
    corpus = tmp_path / "corpus.yaml"
    corpus.write_text(yaml.safe_dump({
        "literature_corpus": [
            {"citation_key": "alpha", "title": "Alpha", "authors": [{"family": "Smith"}],
             "year": 2024, "source_pointer": "doi:10.1/alpha", "doi": "10.1/alpha"},
        ]
    }))
    out = tmp_path / "timeline.yaml"
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--corpus", str(corpus),
         "--output", str(out),
         "--dry-run"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr}"
    assert out.exists()
    data = yaml.safe_load(out.read_text())
    assert data["schema_version"] == "1.0"
    sources = data["sources"]
    assert len(sources) == 1
    assert sources[0]["citation_key"] == "alpha"
    # Dry run: published_date.method should NOT be crossref_lookup (no API call)
    # Acceptable: either falls back to corpus year (method: adapter_metadata) OR absent
    pd = sources[0].get("published_date")
    if pd is not None:
        assert pd.get("provenance", {}).get("method") != "crossref_lookup"


def test_bootstrap_validates_against_timeline_schema(tmp_path):
    """Generated timeline.yaml must validate against timeline.schema.json."""
    import jsonschema
    corpus = tmp_path / "corpus.yaml"
    corpus.write_text(yaml.safe_dump({
        "literature_corpus": [
            {"citation_key": "alpha", "title": "Alpha", "authors": [{"family": "Smith"}],
             "year": 2024, "source_pointer": "doi:10.1/alpha", "doi": "10.1/alpha"},
        ]
    }))
    out = tmp_path / "timeline.yaml"
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--corpus", str(corpus),
         "--output", str(out),
         "--dry-run"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    data = yaml.safe_load(out.read_text())
    schema = json.loads((REPO_ROOT / "shared/contracts/passport/timeline.schema.json").read_text())
    jsonschema.validate(data, schema)  # should not raise
