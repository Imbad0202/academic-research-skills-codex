"""Full reviewer coverage cannot pass after a functional seat is omitted."""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reviewer_coverage_gates", ROOT / "scripts" / "ars_codex_quality_gates.py"
)
GATES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATES)
FIXTURE = ROOT / "tests" / "fixtures" / "reviewer_full_independent_sections.md"


@pytest.mark.parametrize("seat", [
    "Journal-Fit", "Methodology", "Domain", "Interdisciplinary", "Devil's Advocate",
])
def test_each_seat_is_required_before_synthesis(tmp_path, seat):
    text = FIXTURE.read_text()
    start = text.index(f"## Independent Reviewer: {seat}")
    end = text.index("\n## ", start)
    path = tmp_path / "review.md"
    path.write_text(text[:start] + text[end:])
    with pytest.raises(GATES.GateFailure, match="requires one heading"):
        GATES.check_reviewer_fixture(path)


def test_synthesis_cannot_precede_journal_fit(tmp_path):
    text = FIXTURE.read_text()
    start = text.index("## Independent Reviewer: Journal-Fit")
    end = text.index("## Independent Reviewer: Methodology")
    journal_fit = text[start:end]
    text = text[:start] + text[end:] + "\n" + journal_fit
    path = tmp_path / "review.md"
    path.write_text(text)
    with pytest.raises(GATES.GateFailure, match="synthesis must appear after"):
        GATES.check_reviewer_fixture(path)


def test_all_five_seats_and_dissent_are_preserved():
    assert GATES.check_reviewer_fixture(FIXTURE)
