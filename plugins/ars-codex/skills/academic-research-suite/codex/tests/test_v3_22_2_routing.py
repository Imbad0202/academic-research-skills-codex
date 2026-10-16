"""Codex boundaries for the v3.22.2 routing and caller contracts.

These tests exercise deterministic planning and prompt packaging, not live model
compliance with the workflow instructions.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


CODEX_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = CODEX_ROOT.parent
PLANNER_PATH = CODEX_ROOT / "scripts/ars_codex_full_runtime.py"
FIXTURES = SUITE_ROOT / "ars/tests/fixtures/issue_133_routing"


def planner():
    spec = importlib.util.spec_from_file_location("routing_3_22_2", PLANNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("alias,mode", [
    ("ars-plan", "plan"), ("ars-outline", "outline-only"),
    ("ars-abstract", "abstract-only"), ("ars-lit-review", "lit-review"),
    ("ars-full", "pipeline"),
])
def test_explicit_alias_survives_vague_topic_and_missing_inputs(alias, mode):
    plan = planner().plan_request(
        f"/{alias} I want to write a paper on education. I have no research question or sources yet.",
        env={},
    )
    assert plan["routing_status"] == "routed"
    assert plan["mode"] == mode
    assert plan["workflow"] == ("academic-pipeline" if alias == "ars-full" else "academic-paper")
    assert plan["route_reason"] == "alias_router"
    assert plan["dispatch_request"].startswith("I want to write")
    assert not plan["dispatch_request"].startswith(f"/{alias}")


@pytest.mark.parametrize("task_request,workflow,mode", [
    ("Draft an abstract. I want to write a paper on education, without a research question.", "academic-paper", "abstract-only"),
    ("Write an outline for my paper; sources are still missing.", "academic-paper", "outline-only"),
    ("Enmienda mi artículo. Aún no tengo los comentarios de los revisores.", "academic-paper", "revision"),
    ("Revise my manuscript; there are no reviewer comments.", "academic-paper", "revision"),
    ("Revisar artículo sobre revisión de literatura.", "academic-paper-reviewer", "full"),
    ("Run lit-review on these papers, which I have not uploaded.", "academic-paper", "lit-review"),
    ("Full pipeline. I want to write a paper on education, without a research question.", "academic-pipeline", "pipeline"),
])
def test_explicit_natural_mode_keeps_its_usual_missing_input_handling(task_request, workflow, mode):
    plan = planner().plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == (workflow, mode)
    assert plan["routing_status"] == "routed"


@pytest.mark.parametrize("case", [
    "01_cross_phase_abstract_plus_lit",
    "03_no_materials_ambiguous",
    "06_direct_mode_mid_message_not_honored",
    "08_full_draft_plus_abstract_plus_lit",
])
def test_upstream_ambiguous_fixtures_never_plan_dispatch(case):
    plan = planner().plan_request((FIXTURES / case / "input.md").read_text(), env={
        "ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1",
    })
    assert plan["routing_status"] == "clarification_required"
    assert plan["workflow"] is None and plan["mode"] is None
    assert plan["direct_mode_honored"] is False
    assert plan["agent_team_plan"] == []
    assert plan["topology_plan"]["execution_blocked"] is True
    assert plan["topology_plan"]["nodes"] == []
    assert plan["model_plan"] is None


@pytest.mark.parametrize("task_request", [
    "Here are an abstract and a literature review. Please help.",
    "Can you help me with my paper?\n\n> /ars-reviewer Review my manuscript.",
    "Please help.\n```text\nars-reviewer review this paper\n```",
    "The example command is `ars-lit-review`; I have an abstract draft and 25 papers.",
    "Hi, please run bibliography_agent. I have an abstract draft and 25 PDFs.",
])
def test_materials_and_examples_do_not_become_mode_invocations(task_request):
    plan = planner().plan_request(task_request, env={})
    assert plan["routing_status"] == "clarification_required"
    assert plan["command_alias"] is None
    assert plan["agent_team_plan"] == []


def test_explicit_route_wins_over_cross_phase_materials():
    plan = planner().plan_request(
        "Review my manuscript. I have an abstract draft, 25 papers, and reviewer comments.", env={},
    )
    assert (plan["workflow"], plan["mode"]) == ("academic-paper-reviewer", "full")


@pytest.mark.parametrize("prefix", ["[direct-mode]", " [Direct-Mode] ", "\n\t[DIRECT-MODE]\n"])
def test_direct_mode_strips_only_byte_zero_token_and_narrows_named_agent(prefix):
    task_request = "run bibliography_agent on these 30 PDFs about scaling laws"
    plan = planner().plan_request(prefix + task_request, env={
        "ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1",
    })
    assert plan["direct_mode_honored"] is True
    assert plan["dispatch_request"] == task_request
    assert plan["direct_agent_path"] == "ars/deep-research/agents/bibliography_agent.md"
    assert plan["direct_agent_path"] in plan["required_read_paths"]
    assert plan["mode"] == "direct-agent"
    assert plan["agent_team_plan"] == []
    assert all(node["agent"] not in {"pipeline_orchestrator_agent", "eic_agent"}
               for node in plan["topology_plan"]["nodes"])


def test_direct_mode_target_without_inputs_still_loads_role():
    plan = planner().plan_request("[direct-mode] bibliography_agent", env={})
    assert plan["routing_status"] == "routed"
    assert plan["direct_agent_path"] in plan["required_read_paths"]
    assert plan["required_read_status"] == "caller_must_read_before_execution"


@pytest.mark.parametrize("task_request", ["[direct-mode] please help", "[direct-mode]", "[direct-mode] socratic_mentor_agent"])
def test_direct_mode_without_an_unambiguous_target_still_clarifies(task_request):
    plan = planner().plan_request(task_request, env={})
    assert plan["direct_mode_honored"] is True
    assert plan["routing_status"] == "clarification_required"
    assert plan["topology_plan"]["execution_blocked"] is True


def test_direct_mode_natural_abstract_and_named_workflow():
    plan = planner().plan_request((FIXTURES / "07_direct_mode_case_insensitive/input.md").read_text(), env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-paper", "abstract-only")
    assert "[Direct-Mode]" not in plan["dispatch_request"]
    plan = planner().plan_request("[direct-mode] academic-paper-reviewer", env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-paper-reviewer", "full")


def test_skill_prefix_alias_is_preserved_without_accepting_embedded_aliases():
    plan = planner().plan_request("Use $academic-research-suite. /ars-citation-check Chinese APA 7 references.", env={})
    assert plan["command_alias"] == "ars-citation-check"
    assert plan["dispatch_request"] == "Chinese APA 7 references."
    assert "ars/academic-paper/references/apa7_chinese_citation_guide.md" in plan["required_read_paths"]
    mentioned = planner().plan_request("The alias ars-reviewer is available. Can you help?", env={})
    assert mentioned["command_alias"] is None
    assert mentioned["routing_status"] == "clarification_required"


@pytest.mark.parametrize("task_request", [
    "Check my citations.", "Verify references.", "Look over the refs.",
    "Citation check for this manuscript.", "請檢查引用。", "請引用檢查。",
    "檢查參考文獻。", "核對文獻。", "检查参考文献。", "인용 확인 부탁해.",
    "인용 형식 검사 해줘.", "Verificar citas de este borrador.",
])
def test_multilingual_citation_requests_load_the_compliance_prompt(task_request):
    plan = planner().plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-paper", "citation-check")
    assert "ars/academic-paper/agents/citation_compliance_agent.md" in plan["required_read_paths"]


def test_chinese_apa_citation_requests_also_load_locale_guide():
    plan = planner().plan_request("請檢查中文 APA 7 引用及參考文獻。", env={})
    assert "ars/academic-paper/references/apa7_chinese_citation_guide.md" in plan["required_read_paths"]


def test_cli_serializes_clarification_without_dispatch():
    result = subprocess.run(
        [sys.executable, str(PLANNER_PATH), "Can you help me with my paper?", "--pretty"],
        capture_output=True, text=True, check=True,
    )
    plan = json.loads(result.stdout)
    assert plan["routing_status"] == "clarification_required"
    assert plan["workflow"] is None
    assert plan["topology_plan"]["execution_blocked"] is True


def test_caller_contracts_preserve_loading_and_advisory_boundaries():
    skill = (SUITE_ROOT / "SKILL.md").read_text()
    for phrase in (
        "never the paper project's working directory",
        "required supporting file cannot be loaded",
        "command summary is not a substitute",
        "run_ledger.py append",
        "step_outcomes",
        "Keep the ledger local",
        "check_acronyms.py",
        "Phase 4b reports never enter the Phase 6a/6b evaluator",
        "No decision, roadmap, response",
        "partial` and `not_checked",
    ):
        assert phrase in skill


def test_direct_mode_only_applies_to_the_first_user_message():
    plan = planner().plan_request(
        "[direct-mode] run bibliography_agent", env={}, first_message=False,
    )
    assert plan["direct_mode_honored"] is False
    assert plan["routing_status"] == "clarification_required"
    assert plan["dispatch_request"] == "run bibliography_agent"


def test_cli_can_disable_first_message_direct_mode():
    result = subprocess.run(
        [sys.executable, str(PLANNER_PATH), "--not-first-message", "[direct-mode] bibliography_agent"],
        capture_output=True, text=True, check=True,
    )
    plan = json.loads(result.stdout)
    assert plan["direct_mode_honored"] is False
    assert plan["routing_status"] == "clarification_required"


@pytest.mark.parametrize("task_request", [
    "Run the full pipeline and draft an abstract for the final paper.",
    "I want the full pipeline for a systematic review.",
    "Start the full research-to-paper pipeline; then check citations.",
])
def test_explicit_end_to_end_workflow_owns_its_component_modes(task_request):
    plan = planner().plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-pipeline", "pipeline")


@pytest.mark.parametrize("task_request", [
    "Please help.\n~~~text\nReview my manuscript.\n~~~",
    "Please help.\n````text\nReview my manuscript.\n```\n````",
    "Here are an abstract and bibliography. The reviewer wrote “draft an abstract”. Please help.",
    'Here are an abstract and bibliography. The reviewer wrote "draft an abstract". Please help.',
])
def test_quoted_and_fenced_material_cannot_schedule_roles(task_request):
    plan = planner().plan_request(task_request, env={
        "ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1",
    })
    assert plan["routing_status"] == "clarification_required"
    assert plan["topology_plan"]["nodes"] == []
    assert plan["agent_team_plan"] == []


def test_direct_named_workflow_retains_narrower_requested_mode():
    plan = planner().plan_request("[direct-mode] academic-paper citation-check", env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-paper", "citation-check")
    assert "ars/academic-paper/agents/citation_compliance_agent.md" in plan["required_read_paths"]


def test_direct_reviewer_role_has_no_full_panel_template_or_workflow_node():
    plan = planner().plan_request("[direct-mode] academic-paper-reviewer field_analyst_agent", env={
        "ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1",
    })
    assert plan["agent_template"] is None
    assert plan["agent_team_plan"] == []
    assert plan["topology_plan"]["scope"] == "direct_agent_only"
    assert len(plan["topology_plan"]["nodes"]) == 1
    node = plan["topology_plan"]["nodes"][0]
    assert node["agent"] == "field_analyst_agent"
    assert node["prompt_path"] == plan["direct_agent_path"]
    assert "workflow_result" not in node["emits"]
