from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


CODEX_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = CODEX_ROOT.parent
PLANNER_PATH = CODEX_ROOT / "scripts" / "ars_codex_full_runtime.py"
GATES_PATH = CODEX_ROOT / "scripts" / "ars_codex_quality_gates.py"
MODEL_TIERING_CHECK = SUITE_ROOT / "ars" / "scripts" / "check_model_tiering.py"


def _load_planner():
    spec = importlib.util.spec_from_file_location("ars_codex_full_runtime", PLANNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_vague_paper_topic_routes_to_deep_research_socratic() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "Use $academic-research-suite. I want to write a paper on AI adoption in higher education quality assurance. I do not yet have a clear research question.",
        env={},
    )
    assert plan["workflow"] == "deep-research"
    assert plan["mode"] == "socratic"
    assert plan["route_reason"] == "paper_topic_scoping_override"


def test_explicit_empty_env_never_inherits_process_runtime_flags(monkeypatch) -> None:
    planner = _load_planner()
    monkeypatch.setenv("ARS_CODEX_FULL_RUNTIME", "1")
    monkeypatch.setenv("ARS_CODEX_AGENT_TEAM", "1")
    plan = planner.plan_request("ars-reviewer full review for this manuscript.", env={})
    assert plan["profile"]["agent_team_enabled"] is False
    assert plan["topology_plan"]["arm_id"] == "inline-solo"
    assert plan["agent_team_plan"] == []


def test_vague_topic_with_unclear_research_question_still_routes_to_socratic() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "Use $academic-research-suite. I want to write a paper on AI governance in universities, but my research question is still unclear.",
        env={},
    )
    assert plan["workflow"] == "deep-research"
    assert plan["mode"] == "socratic"
    assert plan["route_reason"] == "paper_topic_scoping_override"


def test_ars_plan_routes_to_academic_paper_plan_when_rq_exists() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-plan Research question: How do QA agencies evaluate AI governance in universities?",
        env={},
    )
    assert plan["command_alias"] == "ars-plan"
    assert plan["workflow"] == "academic-paper"
    assert plan["mode"] == "plan"
    assert plan["command_recipe"] == "ars/commands/ars-plan.md"


def test_ars_lit_review_alias_routes_to_lit_review_mode() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-lit-review Research question: What is known about AI governance in university QA?",
        env={},
    )
    assert plan["workflow"] == "academic-paper"
    assert plan["mode"] == "lit-review"


def test_ars_cache_invalidate_alias_routes_to_pipeline_cache_mode() -> None:
    planner = _load_planner()
    plan = planner.plan_request("ars-cache-invalidate smith2024", env={})
    assert plan["command_alias"] == "ars-cache-invalidate"
    assert plan["workflow"] == "academic-pipeline"
    assert plan["mode"] == "cache-invalidate"
    assert plan["command_recipe"] == "ars/commands/ars-cache-invalidate.md"


def test_ars_3w_alias_routes_to_deep_research_three_way_scan() -> None:
    planner = _load_planner()
    plan = planner.plan_request("ars-3w compare these three papers", env={})
    assert plan["command_alias"] == "ars-3w"
    assert plan["workflow"] == "deep-research"
    assert plan["mode"] == "three-way-scan"
    assert plan["command_recipe"] == "ars/commands/ars-3w.md"


def test_ars_rebuttal_audit_alias_routes_to_academic_paper() -> None:
    planner = _load_planner()
    plan = planner.plan_request("ars-rebuttal-audit check my response draft against these reviewer comments", env={})
    assert plan["command_alias"] == "ars-rebuttal-audit"
    assert plan["workflow"] == "academic-paper"
    assert plan["mode"] == "rebuttal-audit"
    assert plan["command_recipe"] == "ars/commands/ars-rebuttal-audit.md"


def test_korean_revision_routes_to_academic_paper_not_reviewer() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "이 논문을 수정해줘. 심사 의견은 아직 없고, 초고를 더 다듬고 싶어.",
        env={},
    )
    assert plan["workflow"] == "academic-paper"
    assert plan["mode"] == "revision"


def test_korean_review_routes_to_reviewer_not_revision() -> None:
    planner = _load_planner()
    plan = planner.plan_request("이 논문을 심사해줘.", env={})
    assert plan["workflow"] == "academic-paper-reviewer"
    assert plan["mode"] == "full"


def test_model_tiering_is_surfaced_without_forcing_a_codex_model() -> None:
    planner = _load_planner()
    inline = planner.plan_request("ars-plan Research question: Why?", env={"ARS_MODEL_TIERING": "economy"})
    assert inline["profile"]["model_tiering_status"] == "inline_noop"

    delegated = planner.plan_request(
        "ars-plan Research question: Why?",
        env={
            "ARS_CODEX_FULL_RUNTIME": "1",
            "ARS_CODEX_AGENT_TEAM": "1",
            "ARS_MODEL_TIERING": "quality-boost",
        },
    )
    assert delegated["profile"]["model_tiering_status"] == "advisory_requires_runtime_model_override"
    assert delegated["profile"]["model_tiering_requested"] == "quality-boost"


def test_cross_model_configuration_requires_dispatcher_consent_gate() -> None:
    planner = _load_planner()
    inline = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={"ARS_CROSS_MODEL": "gpt-5.5"},
    )
    assert inline["profile"]["cross_model_configured"] == "gpt-5.5"
    assert inline["profile"]["cross_model_handoff_status"] == (
        "inline_transport_requires_explicit_request_and_consent"
    )

    delegated = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={
            "ARS_CODEX_FULL_RUNTIME": "1",
            "ARS_CODEX_AGENT_TEAM": "1",
            "ARS_CROSS_MODEL": "gpt-5.5",
        },
    )
    assert delegated["profile"]["cross_model_handoff_status"] == (
        "dispatcher_transport_requires_explicit_request_and_consent"
    )
    reviewer_2 = next(
        item
        for item in delegated["agent_team_plan"]
        if item["agent"] == "domain_reviewer_agent"
    )
    assert reviewer_2["cross_model_reviewer_track"] == (
        "configured_requires_explicit_content_consent"
    )


def test_v318_cache_controls_are_surfaced_without_changing_gate_semantics() -> None:
    planner = _load_planner()
    default = planner.plan_request("ars-cache-invalidate smith2024", env={})
    assert default["profile"]["cache_stale_advisory_days"] == 30
    assert default["profile"]["cache_revalidation_status"] == "cached_default"

    requested = planner.plan_request(
        "ars-cache-invalidate smith2024",
        env={"ARS_CACHE_STALE_ADVISORY_DAYS": "0", "ARS_CACHE_REVALIDATE": "1"},
    )
    assert requested["profile"]["cache_stale_advisory_days"] == 0
    assert requested["profile"]["cache_revalidation_requested"] is True
    assert requested["profile"]["cache_revalidation_status"] == (
        "live_bibliographic_revalidation_requested"
    )

    malformed = planner.plan_request(
        "ars-cache-invalidate smith2024",
        env={"ARS_CACHE_STALE_ADVISORY_DAYS": "not-a-number"},
    )
    assert malformed["profile"]["cache_stale_advisory_days"] == 30


def test_ars_full_starts_pipeline_and_stops_at_dashboard_checkpoint() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-full Research question: How do QA agencies evaluate AI governance? Stop after producing the pipeline dashboard.",
        env={"ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1"},
    )
    assert plan["profile"]["execution_mode"] == "codex_agent_team"
    assert plan["workflow"] == "academic-pipeline"
    assert plan["mode"] == "pipeline"
    assert plan["stop_at_checkpoint"] == "pipeline_dashboard"
    assert [item["agent"] for item in plan["agent_team_plan"]][:2] == [
        "pipeline_orchestrator_agent",
        "state_tracker_agent",
    ]
    topology = plan["topology_plan"]
    assert topology["arm_id"] == "workflow-current"
    integrity = next(node for node in topology["nodes"] if node["id"] == "integrity_verification_agent")
    assert integrity["phase"] == "checkpoint_2_5_or_4_5"


def test_reviewer_full_agent_team_records_field_then_blind_panel_then_synthesis() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={"ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1"},
    )
    agents = [item["agent"] for item in plan["agent_team_plan"]]
    assert plan["workflow"] == "academic-paper-reviewer"
    assert plan["mode"] == "full"
    assert "editorial_synthesizer_agent" == agents[-1]
    assert "methodology_reviewer_agent" in agents[:-1]
    assert "devils_advocate_reviewer_agent" in agents[:-1]
    topology = plan["topology_plan"]
    assert topology["arm_id"] == "reviewer-full-seven"
    field = topology["nodes"][0]
    assert field["id"] == "field_analyst_agent"
    assert field["depends_on"] == []
    reviewers = [node for node in topology["nodes"] if node["phase"] == "blind_review"]
    assert len(reviewers) == 5
    assert all(node["depends_on"] == ["field_analyst_agent"] for node in reviewers)
    assert all(not any(value.endswith("_report") for value in node["reads"]) for node in reviewers)
    synth = topology["nodes"][-1]
    assert synth["id"] == "editorial_synthesizer_agent"
    assert set(synth["depends_on"]) == {"field_analyst_agent", *(node["id"] for node in reviewers)}
    assert topology["information_sharing"]["peer_outputs"] == "hidden_until_synthesis"


def test_topology_arm_variable_alone_does_not_enable_experiment() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={"ARS_CODEX_TOPOLOGY_ARM": "reviewer-five-panel"},
    )
    assert plan["profile"]["topology_arm_status"] == "ignored_without_experiment_opt_in"
    assert plan["topology_plan"]["arm_id"] == "inline-solo"
    assert plan["agent_team_plan"] == []


def test_explicit_topology_experiment_requires_agent_team_for_non_inline_arm() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={
            "ARS_CODEX_TOPOLOGY_EXPERIMENT": "1",
            "ARS_CODEX_TOPOLOGY_ARM": "reviewer-two-plus-synthesis",
        },
    )
    assert plan["topology_plan"]["execution_blocked"] is True
    assert "topology_agent_team_runtime_required" in plan["topology_plan"]["reason_codes"]


def test_explicit_reviewer_two_arm_has_two_blind_roots_and_one_sink() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={
            "ARS_CODEX_FULL_RUNTIME": "1",
            "ARS_CODEX_AGENT_TEAM": "1",
            "ARS_CODEX_TOPOLOGY_EXPERIMENT": "1",
            "ARS_CODEX_TOPOLOGY_ARM": "reviewer-two-plus-synthesis",
        },
    )
    topology = plan["topology_plan"]
    assert topology["execution_blocked"] is False
    assert [node["id"] for node in topology["nodes"]] == [
        "methodology_reviewer_agent",
        "domain_reviewer_agent",
        "editorial_synthesizer_agent",
    ]
    assert len(topology["edges"]) == 2
    assert all(edge["to"] == "editorial_synthesizer_agent" for edge in topology["edges"])
    assert {tuple(edge["artifacts"]) for edge in topology["edges"]} == {
        ("methodology_reviewer_agent_report",),
        ("domain_reviewer_agent_report",),
    }


def test_cli_outputs_json_plan() -> None:
    result = subprocess.run(
        [sys.executable, str(PLANNER_PATH), "ars-reviewer", "full", "review"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["workflow"] == "academic-paper-reviewer"
    assert payload["mode"] == "full"


def test_quality_gates_all_pass() -> None:
    result = subprocess.run(
        [sys.executable, str(GATES_PATH), "all", "--json"],
        cwd=SUITE_ROOT.parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert all(item["ok"] for item in payload.values()), payload


def test_model_tiering_lint_accepts_separately_vendored_experiment_agents() -> None:
    result = subprocess.run(
        [sys.executable, str(MODEL_TIERING_CHECK)],
        cwd=SUITE_ROOT / "ars",
        check=True,
        capture_output=True,
        text=True,
    )
    assert "39 agents classified" in result.stdout
