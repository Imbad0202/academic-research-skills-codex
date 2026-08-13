from __future__ import annotations

import importlib.util
from pathlib import Path


CODEX_ROOT = Path(__file__).resolve().parents[1]
RUNNER = CODEX_ROOT / "scripts" / "ars_codex_topology_experiment.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("ars_codex_topology_experiment", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_frozen_cohort_has_exactly_ten_tasks_and_twenty_six_runs() -> None:
    runner = _load_runner()
    result = runner.validate_all(require_runs=False)
    assert result == {
        "schema": "ars.codex.topology-validation.v1",
        "status": "PASS",
        "task_count": 10,
        "run_count": result["run_count"],
        "expected_run_count": 26,
        "reason_codes": [],
    }


def test_every_frozen_input_digest_recomputes_from_allowlisted_files() -> None:
    runner = _load_runner()
    cohort = runner.load_cohort()
    for task in cohort["tasks"]:
        assert runner.task_input_digest(task) == task["input_digest"]
        assert all("expected_" not in item["source"] for item in task["inputs"])
        assert all("good_run" not in item["source"] for item in task["inputs"])


def test_all_registered_topologies_are_acyclic_and_have_existing_parents() -> None:
    runner = _load_runner()
    cohort = runner.load_cohort()
    for task in cohort["tasks"]:
        for arm_id in task["arms"]:
            assert runner.validate_dag(runner.plan_for(task, arm_id)) == []


def test_reviewer_blind_arms_have_no_reviewer_to_reviewer_edges() -> None:
    runner = _load_runner()
    cohort = runner.load_cohort()
    task = runner.task_by_id(cohort, "ms01_quant")
    for arm_id in ("reviewer-two-plus-synthesis", "reviewer-five-panel", "reviewer-full-seven"):
        plan = runner.plan_for(task, arm_id)
        reviewer_ids = {node["id"] for node in plan["nodes"] if node["phase"] == "blind_review"}
        assert not any(edge["from"] in reviewer_ids and edge["to"] in reviewer_ids for edge in plan["edges"])
        assert plan["information_sharing"]["peer_outputs"] == "hidden_until_synthesis"
        for edge in plan["edges"]:
            if edge["from"] in reviewer_ids:
                assert edge["artifacts"] == [f"{edge['from']}_report"]


def test_unknown_resource_metrics_never_become_zero() -> None:
    runner = _load_runner()
    assert runner.metric(None) == {"state": "unknown", "value": None}
    assert runner.metric(0) == {"state": "known", "value": 0}


def test_receipt_rejects_missing_duplicate_and_unknown_coercion() -> None:
    runner = _load_runner()
    cohort = runner.load_cohort()
    task = runner.task_by_id(cohort, "A1")
    result = runner.load_json(runner.RUNS_ROOT / "A1--inline-solo.json")
    envelope = result["envelope"]
    receipt = runner.load_json(runner.RECEIPTS_ROOT / "A1--inline-solo.json")
    assert runner.validate_receipt(receipt, envelope) == []

    missing = dict(receipt)
    missing["agent_receipts"] = []
    assert "agent_receipts_mismatch" in runner.validate_receipt(missing, envelope)

    duplicate = dict(receipt)
    duplicate["agent_receipts"] = receipt["agent_receipts"] * 2
    assert "agent_receipts_mismatch" in runner.validate_receipt(duplicate, envelope)

    coerced = runner.load_json(runner.RECEIPTS_ROOT / "A1--inline-solo.json")
    coerced["usage"]["provider_calls"] = {"state": "unknown", "value": 0}
    assert "unknown_measurement_has_value" in runner.validate_receipt(coerced, envelope)


def test_complete_result_set_has_exact_envelopes_and_receipts() -> None:
    runner = _load_runner()
    result = runner.validate_all(require_runs=True)
    assert result["status"] == "PASS", result
    assert result["run_count"] == result["expected_run_count"] == 26


def test_report_keeps_evidence_dimensions_separate_and_default_inline() -> None:
    runner = _load_runner()
    report = runner.build_report()
    assert report["status"] == "EXPLORATORY_COMPLETE"
    assert report["run_count"] == 26
    assert report["local_go_no_go"]["changes_default_routing"] is False
    for workflow in ("reviewer", "pipeline"):
        for arm in report["evidence"][workflow].values():
            assert set(arm) == {
                "task_count",
                "outcome_quality",
                "coordination_cost",
                "duplicate_contributions",
                "verifier_catches",
            }
            assert arm["verifier_catches"] == {"state": "unknown", "value": None}


def test_report_is_canonical_and_has_no_winner_or_routing_mutation_fields() -> None:
    runner = _load_runner()
    first = runner.build_report()
    second = runner.build_report()
    assert runner.canonical_json(first) == runner.canonical_json(second)
    forbidden = {"winner", "recommended_topology", "routing_decision", "paper_threshold"}
    assert forbidden.isdisjoint(first)


def test_every_matched_identity_dimension_fails_closed_with_specific_reason() -> None:
    runner = _load_runner()
    cohort = runner.load_cohort()
    task = runner.task_by_id(cohort, "A1")
    envelope = runner.experiment_envelope(cohort, task, "inline-solo", "codex-cli 0.146.0")
    control = envelope["identity"]
    mutations = {
        "baseline_commit": "code_baseline_mismatch",
        "input_digest": "input_mismatch",
        "dataset_digest": "dataset_mismatch",
        "evaluator_digest": "evaluator_mismatch",
        "environment_digest": "environment_mismatch",
        "model_allowance_digest": "model_mismatch",
        "tool_allowance_digest": "tool_mismatch",
        "outcome_metric": "metric_mismatch",
        "trajectory": "trajectory_mismatch",
        "budget": "budget_mismatch",
        "retry_policy": "retry_mismatch",
        "seeds": "seeds_mismatch",
    }
    for key, expected_reason in mutations.items():
        candidate = dict(control)
        candidate[key] = {"mutated": True} if isinstance(control[key], dict) else "mutated"
        assert runner.matched_identity_reason_codes(control, candidate) == [expected_reason]
