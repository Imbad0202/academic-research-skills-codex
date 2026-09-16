"""Release parity and Spanish routing boundaries introduced in ARS 3.22."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


CODEX_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = CODEX_ROOT.parent


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, CODEX_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("fixture", "workflow", "mode"),
    [
        ("11_spanish_revision_not_review", "academic-paper", "revision"),
        ("12_spanish_review_not_revision", "academic-paper-reviewer", "full"),
    ],
)
def test_spanish_upstream_boundary_fixtures(fixture, workflow, mode):
    request = (SUITE_ROOT / "ars/tests/fixtures/issue_133_routing" / fixture / "input.md").read_text()
    plan = load_script("ars_codex_full_runtime").plan_request(request, env={})
    assert (plan["workflow"], plan["mode"]) == (workflow, mode)


@pytest.mark.parametrize(
    ("task_request", "workflow", "mode"),
    [
        ("Haz una revisión de literatura sobre tutoría.", "deep-research", "lit-review"),
        ("Revisión sistemática de revisión entre docentes.", "deep-research", "systematic-review"),
        ("Guía mi investigación sobre educación.", "deep-research", "socratic"),
        ("Flujo de trabajo académico completo.", "academic-pipeline", "pipeline"),
        ("Recibí comentarios de revisores; prepara una ruta de revisión.", "academic-paper", "revision-coach"),
        ("Escribir resumen para el manuscrito adjunto.", "academic-paper", "abstract-only"),
        ("Verificar citas de este borrador.", "academic-paper", "citation-check"),
        ("Convertir formato de este manuscrito a LaTeX.", "academic-paper", "format-convert"),
        ("Planificar un artículo de revisión bibliográfica.", "academic-paper", "lit-review"),
        ("Quiero escribir un artículo sobre educación, sin una pregunta de investigación clara.", "deep-research", "socratic"),
        ("Quiero escribir un artículo sobre educación. Pregunta de investigación: ¿Cómo influye la tutoría en la retención?", "academic-paper", "plan"),
        ("Revisión del presupuesto del viaje.", "academic-paper", "plan"),
    ],
)
def test_spanish_compounds_keep_route_boundaries(task_request, workflow, mode):
    plan = load_script("ars_codex_full_runtime").plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == (workflow, mode)


def test_package_gate_rejects_drifted_upstream_suite(tmp_path, monkeypatch):
    gates = load_script("ars_codex_quality_gates")
    pipeline = tmp_path / "academic-pipeline"
    pipeline.mkdir()
    (pipeline / "WORKFLOW.md").write_text('---\nmetadata:\n  version: "0.0.0"\n---\n')
    monkeypatch.setattr(gates, "ARS_ROOT", tmp_path)
    with pytest.raises(gates.GateFailure, match="upstream suite version"):
        gates.check_manifest()


@pytest.mark.parametrize("field", ["version", "tag"])
def test_package_gate_rejects_drifted_source_release(tmp_path, monkeypatch, field):
    gates = load_script("ars_codex_quality_gates")
    package = json.loads(gates.PACKAGE_MANIFEST.read_text())
    package["source_repositories"][0][field] = "0.0.0"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(package))
    monkeypatch.setattr(gates, "PACKAGE_MANIFEST", path)
    with pytest.raises(gates.GateFailure, match="source version/tag"):
        gates.check_manifest()
