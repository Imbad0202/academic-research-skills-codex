"""Model-selection boundaries: recommendation, override, and observed execution."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


PLANNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ars_codex_full_runtime.py"


def planner():
    spec = importlib.util.spec_from_file_location("ars_model_policy_planner", PLANNER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("task_request", "effort"),
    [
        ("ars-abstract Research question: How does feedback affect learning?", "medium"),
        ("ars-citation-check verify this reference", "medium"),
        ("ars-cache-invalidate smith2024", "medium"),
        ("ars-lit-review Research question: How does feedback affect learning?", "xhigh"),
        ("ars-reviewer review this manuscript", "xhigh"),
        ("ars-full Research question: How does feedback affect learning?", "xhigh"),
    ],
)
def test_route_policy_selects_effort_without_reusing_claude_frontmatter(task_request, effort):
    plan = planner().plan_request(task_request, env={})
    model = plan["model_plan"]
    assert model["target_model"] == "gpt-6-astra"
    assert model["target_reasoning_effort"] == effort
    assert model["quality_policy_evidence"] == "repository_policy_not_measured_optimum"
    assert model["launch_argv"] == [
        "codex", "--model", "gpt-6-astra", "-c", f'model_reasoning_effort="{effort}"'
    ]


def test_native_adaptive_policy_does_not_enable_fixed_topology_or_hooks():
    plan = planner().plan_request("ars-reviewer review this manuscript", env={})
    assert plan["profile"]["execution_mode"] == "native_adaptive"
    assert plan["profile"]["native_delegation_policy"] == "useful_independent_subtasks_when_runtime_available"
    assert plan["profile"]["fixed_topology_opt_in"] is False
    assert plan["profile"]["hooks_enabled"] is False
    assert plan["agent_team_plan"] == []
    assert plan["topology_plan"]["arm_id"] == "inline-solo"
    assert not plan["degraded_behavior"]


@pytest.mark.parametrize(
    "task_request",
    [
        "Please complete the review. The research question, manuscript, data, and current review criteria are already confirmed.",
        "請完成論文審查，RQ、資料與審查準則都已確認。",
        "請審閱這篇論文，研究問題及審查準則已確認。",
        "Please review this manuscript about systematic reviews.",
    ],
)
def test_natural_manuscript_review_with_confirmed_inputs_uses_judgment_policy(task_request):
    plan = planner().plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-paper-reviewer", "full")
    assert plan["route_reason"] == "natural_review_request"
    assert plan["model_plan"]["target_reasoning_effort"] == "xhigh"


@pytest.mark.parametrize(
    "task_request",
    [
        "Please format-convert this existing paper to DOCX and only output the converted file.",
        "Convert this literature review to PDF.",
        "Could you export the manuscript as Word?",
        "請將這篇論文轉檔成 DOCX，只輸出轉換後的檔案。",
    ],
)
def test_natural_conversion_keeps_routine_effort_and_does_not_schedule_package_gates(task_request):
    plan = planner().plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == ("academic-paper", "format-convert")
    assert plan["model_plan"]["target_reasoning_effort"] == "medium"
    assert plan["quality_gates"]  # Retained for consumers that inspect the catalog.
    assert plan["quality_gate_scope"] == "package_validation_catalog"
    assert plan["quality_gates_execute_on_request"] is False
    assert not plan["profile"]["hooks_enabled"]


@pytest.mark.parametrize(
    ("task_request", "workflow", "mode"),
    [
        ("Please complete the literature review on feedback in education.", "deep-research", "lit-review"),
        ("Please complete the review of the literature on feedback.", "deep-research", "lit-review"),
        ("Please conduct a systematic review of peer review practices.", "deep-research", "systematic-review"),
        ("請完成系統性文獻回顧。", "deep-research", "systematic-review"),
        ("Plan a literature review about DOCX format-conversion tools.", "deep-research", "lit-review"),
        ("Research question: How do format-convert tools affect review quality?", "academic-paper", "plan"),
        ("The current review criteria are confirmed. Please plan the paper.", "academic-paper", "plan"),
        ("Preview this paper outline.", "academic-paper", "plan"),
        ("I want to write a paper on AI governance. I do not yet have a research question.", "deep-research", "socratic"),
        ("I want to write a paper on AI governance. The research question is already confirmed.", "academic-paper", "plan"),
    ],
)
def test_natural_route_does_not_confuse_research_review_or_incidental_words(task_request, workflow, mode):
    plan = planner().plan_request(task_request, env={})
    assert (plan["workflow"], plan["mode"]) == (workflow, mode)


def test_caller_observation_never_becomes_target_or_execution_attestation():
    model = planner().plan_request(
        "ars-reviewer review this manuscript",
        env={"ARS_CODEX_ACTIVE_MODEL": "gpt-5.6-sol", "ARS_CODEX_ACTIVE_REASONING_EFFORT": "low"},
    )["model_plan"]
    assert model["target_model"] == "gpt-6-astra"
    assert model["target_reasoning_effort"] == "xhigh"
    assert model["current_runtime_observation"] == {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "low",
        "source": "caller_reported",
        "independently_verified": False,
    }
    assert model["application_status"] == "planned_only_current_session_unchanged"
    assert model["launch_executed"] is False
    assert model["capability_evidence"]["api_live_validation"] == "not_run"


@pytest.mark.parametrize("effort", ["low", "high", "max", "ultra"])
def test_explicit_effort_overrides_task_and_routine_role_defaults(effort):
    plan = planner().plan_request(
        "ars-reviewer review this manuscript",
        env={"ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1", "ARS_CODEX_REASONING_EFFORT": effort},
    )
    assert plan["model_plan"]["effort_source"] == "explicit_effort_override"
    assert plan["model_plan"]["target_reasoning_effort"] == effort
    assert all(row["model_selection"]["reasoning_effort"] == effort for row in plan["agent_team_plan"])
    assert all(row["model_selection"]["observed_model"] is None for row in plan["agent_team_plan"])
    assert plan["model_plan"]["api_effort_mapping"] == "none_codex_values_are_not_api_authority"


def test_fixed_panel_preserves_blind_dependencies_with_role_effort_targets():
    plan = planner().plan_request(
        "ars-reviewer review this manuscript",
        env={"ARS_CODEX_FULL_RUNTIME": "1", "ARS_CODEX_AGENT_TEAM": "1"},
    )
    rows = {row["agent"]: row for row in plan["agent_team_plan"]}
    assert rows["field_analyst_agent"]["model_selection"]["reasoning_effort"] == "medium"
    for name in ("methodology_reviewer_agent", "domain_reviewer_agent", "devils_advocate_reviewer_agent"):
        assert rows[name]["model_selection"]["reasoning_effort"] == "xhigh"
        assert rows[name]["depends_on"] == ["field_analyst_agent"]
        assert not any(item.endswith("_report") for item in rows[name]["reads"])


def test_explicit_different_model_is_not_given_astra_capabilities_or_guessed_effort():
    model = planner().plan_request(
        "ars-reviewer review this manuscript", env={"ARS_CODEX_MODEL": "provider/custom-model"}
    )["model_plan"]
    assert model["target_model"] == "provider/custom-model"
    assert model["selection_source"] == "explicit_model_override"
    assert model["target_reasoning_effort"] is None
    assert model["supported_reasoning_efforts"] == []
    assert model["capability_evidence"] is None
    assert model["launch_argv"] == ["codex", "--model", "provider/custom-model"]


@pytest.mark.parametrize("effort", ["none", "minimal", "MAX", "unknown", 'xhigh"; echo unsafe'])
def test_unsupported_effort_is_visible_configuration_error(effort):
    with pytest.raises(ValueError, match="unsupported ARS_CODEX_REASONING_EFFORT"):
        planner().plan_request("ars-reviewer review this manuscript", env={"ARS_CODEX_REASONING_EFFORT": effort})


def test_unverified_override_model_effort_cannot_silently_fall_back():
    with pytest.raises(ValueError, match="cannot verify ARS_CODEX_REASONING_EFFORT"):
        planner().plan_request(
            "ars-reviewer review this manuscript",
            env={"ARS_CODEX_MODEL": "provider/custom-model", "ARS_CODEX_REASONING_EFFORT": "max"},
        )


def test_cli_plan_is_read_only_and_invalid_effort_emits_no_plan(tmp_path):
    result = subprocess.run(
        [sys.executable, str(PLANNER_PATH), "ars-citation-check", "verify this reference"],
        env={"ARS_CODEX_REASONING_EFFORT": "ultra"}, cwd=tmp_path,
        capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout)["model_plan"]["launch_executed"] is False
    assert list(tmp_path.iterdir()) == []
    bad = subprocess.run(
        [sys.executable, str(PLANNER_PATH), "ars-citation-check", "verify this reference"],
        env={"ARS_CODEX_REASONING_EFFORT": "maximal"}, cwd=tmp_path,
        capture_output=True, text=True, check=False,
    )
    assert bad.returncode != 0
    assert "unsupported ARS_CODEX_REASONING_EFFORT" in bad.stderr
    assert bad.stdout == ""
