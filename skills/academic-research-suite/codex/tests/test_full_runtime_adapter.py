from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


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


def test_command_model_hints_match_upstream_frontmatter_semantics() -> None:
    manifest = json.loads((CODEX_ROOT / "full-runtime-manifest.json").read_text(encoding="utf-8"))
    hints = {
        command["aliases"][1]: command["model_hint"]
        for command in manifest["commands"]
    }

    for alias in ("ars-full", "ars-reviewer", "ars-revision-coach"):
        assert hints.pop(alias) == "inherit"
    assert hints
    assert set(hints.values()) == {"sonnet"}


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


def test_cross_model_transport_selector_surfaces_closed_api_and_unset_states() -> None:
    planner = _load_planner()

    default = planner.plan_request("ars-plan Research question: Why?", env={})
    assert default["profile"]["cross_model_transport_selector"] == "unset"
    assert default["profile"]["cross_model_effective_transport"] == "api"
    assert default["profile"]["cross_model_transport_scope"] == "none"

    api = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={
            "ARS_CROSS_MODEL": "gpt-5.5",
            "ARS_CROSS_MODEL_TRANSPORT": "api",
        },
    )
    assert api["profile"]["cross_model_transport_selector"] == "api"
    assert api["profile"]["cross_model_effective_transport"] == "api"
    assert api["profile"]["cross_model_transport_scope"] == "api_cross_model_workflows"
    assert api["profile"]["cross_model_explicit_consent_required"] is True


def test_codex_transport_is_citation_only_and_excluded_from_reviewer_plan() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-reviewer full review for this manuscript.",
        env={
            "ARS_CODEX_FULL_RUNTIME": "1",
            "ARS_CODEX_AGENT_TEAM": "1",
            "ARS_CROSS_MODEL": "gpt-5.6-sol",
            "ARS_CROSS_MODEL_TRANSPORT": "codex",
        },
    )
    profile = plan["profile"]
    assert profile["cross_model_transport_selector"] == "codex"
    assert profile["cross_model_effective_transport"] == "codex"
    assert profile["cross_model_transport_ready"] is True
    assert profile["cross_model_transport_scope"] == "citation_integrity_only"
    assert profile["cross_model_explicit_consent_required"] is True
    assert profile["cross_model_handoff_status"] == (
        "codex_citation_only_requires_explicit_request_and_consent"
    )
    assert set(profile["cross_model_forbidden_uses"]) == {
        "devils_advocate",
        "reviewer_seat",
        "re_review_judge",
        "general_judgment",
    }

    reviewer_2 = next(
        item
        for item in plan["agent_team_plan"]
        if item["agent"] == "domain_reviewer_agent"
    )
    assert reviewer_2["cross_model_reviewer_track"] == (
        "excluded_codex_transport_is_citation_only"
    )
    devil = next(
        item
        for item in plan["agent_team_plan"]
        if item["agent"] == "devils_advocate_reviewer_agent"
    )
    assert "cross_model_reviewer_track" not in devil


def test_codex_transport_without_ars_cross_model_is_visibly_unavailable() -> None:
    planner = _load_planner()
    plan = planner.plan_request(
        "ars-citation-check verify this reference.",
        env={"ARS_CROSS_MODEL_TRANSPORT": "codex"},
    )
    profile = plan["profile"]
    assert profile["cross_model_effective_transport"] == "codex"
    assert profile["cross_model_transport_ready"] is False
    assert profile["cross_model_transport_scope"] == "none"
    assert profile["cross_model_handoff_status"] == (
        "codex_transport_unavailable_missing_ARS_CROSS_MODEL"
    )


def test_invalid_cross_model_transport_selector_fails_closed() -> None:
    planner = _load_planner()
    for invalid_selector in ("openai", "unset"):
        with pytest.raises(
            ValueError,
            match="expected the variable to be absent, or set to api or codex",
        ):
            planner.plan_request(
                "ars-reviewer full review for this manuscript.",
                env={
                    "ARS_CROSS_MODEL": "gpt-5.5",
                    "ARS_CROSS_MODEL_TRANSPORT": invalid_selector,
                },
            )

    result = subprocess.run(
        [sys.executable, str(PLANNER_PATH), "ars-reviewer", "full", "review"],
        env={"ARS_CROSS_MODEL_TRANSPORT": "openai"},
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "refused to fall through" in result.stderr
    assert not result.stdout


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


def test_v320_manifest_registers_only_hermetic_runtime_contract_gates() -> None:
    manifest = json.loads((CODEX_ROOT / "full-runtime-manifest.json").read_text(encoding="utf-8"))
    options = manifest["runtime_options"]
    transport = options["cross_model_transport"]
    assert transport["allowed_values"] == ["api", "codex"]
    assert transport["variable_may_be_absent"] is True
    assert transport["normalized_absent_label"] == "unset"
    assert transport["codex_scope"] == "citation_integrity_only"
    assert transport["codex_requires_explicit_consent"] is True
    assert transport["codex_requires_ars_cross_model"] is True
    assert transport["codex_min_cli_version"] == "0.147.0"
    assert transport["codex_login_attestation"] == "Logged in using ChatGPT"
    assert set(transport["codex_forbidden_uses"]) >= {
        "devils_advocate",
        "reviewer_seat",
        "re_review_judge",
        "general_judgment",
    }

    pdf = options["pdf_content_classifier"]
    assert pdf["mode"] == "optional_advisory"
    assert pdf["auto_install"] is False
    assert pdf["verdict_scope"] == "STRUCTURE_ONLY"
    assert (SUITE_ROOT / pdf["dependency_file"]).is_file()

    gates = {
        gate["id"]: gate
        for gate in manifest["quality_gates"]
        if gate["id"].startswith("v320_")
    }
    required = {
        "v320_codex_subscription_transport_contract",
        "v320_codex_subscription_transport_runtime",
        "v320_pdf_content_classifier_isolation",
        "v320_phase_e_evidence_rows",
        "v320_revision_roadmap_author_adjudication",
        "v320_post_terminal_adjudication_activity",
        "v320_human_subjects_authority",
        "v320_review_pathway_rule_trace",
        "v320_submission_packet_manifest",
        "v320_human_subjects_reference_migration",
        "v320_human_subjects_content_coverage",
        "v320_bibliographic_integrity_signals",
        "v320_retraction_status",
        "v320_tortured_phrase_advisory",
        "v320_preregistration_cross_document_advisory",
        "v320_review_target_context",
        "v320_review_criteria_binding",
        "v320_committee_correspondence",
    }
    assert required == set(gates)
    for gate in gates.values():
        assert gate["execution"] == "hermetic"
        runner = gate["runner"].removeprefix("upstream:")
        assert (SUITE_ROOT / runner).is_file(), runner

    all_runners = "\n".join(gate["runner"] for gate in manifest["quality_gates"])
    assert "cross_model_smoke_test_codex.sh" not in all_runners
    assert "run_review_criteria_constructive_value.py" not in all_runners


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
