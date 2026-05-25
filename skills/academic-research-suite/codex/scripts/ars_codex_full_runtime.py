#!/usr/bin/env python3
"""Codex full-runtime planner for the Academic Research Suite adapter.

The planner is intentionally deterministic and side-effect free. It does not
spawn agents or execute hooks; it converts a user request plus opt-in runtime
environment into a structured plan that Codex can follow.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
CODEX_ROOT = SCRIPT.parents[1]
SUITE_ROOT = SCRIPT.parents[2]
MANIFEST_PATH = CODEX_ROOT / "full-runtime-manifest.json"

ALIAS_RE = re.compile(r"(?<![\w/-])(/?ars-[a-z-]+)(?![\w-])", re.IGNORECASE)
QUESTION_RE = re.compile(r"\b(research question|rq|hypothesis|hypotheses)\b|研究問題|研究问题|假設|假设", re.IGNORECASE)
UNCLEAR_QUESTION_RE = re.compile(
    r"(do not|don't|does not|doesn't|not yet|without|no)\s+.{0,40}\b(research question|rq|hypothesis|hypotheses)\b|"
    r"尚未.{0,20}(研究問題|研究问题)|沒有.{0,20}(研究問題|研究问题)|没有.{0,20}(研究問題|研究问题)",
    re.IGNORECASE,
)

VAGUE_TOPIC_PATTERNS = (
    "i want to write a paper",
    "i want to write an article",
    "paper on ",
    "paper topic",
    "tentative title",
    "broad topic",
    "research direction",
    "我想做一篇論文",
    "我想做一篇论文",
    "論文題目",
    "论文题目",
    "研究方向",
    "研究主題",
    "研究主题",
    "題目是",
    "题目是"
)

ALIAS_SOC_OVERRIDE = {
    "ars-plan",
    "ars-outline",
    "ars-abstract",
    "ars-lit-review",
    "ars-full",
}

REVIEWER_ORDER = [
    "field_analyst_agent.md",
    "eic_agent.md",
    "methodology_reviewer_agent.md",
    "domain_reviewer_agent.md",
    "perspective_reviewer_agent.md",
    "devils_advocate_reviewer_agent.md",
    "editorial_synthesizer_agent.md",
]

PIPELINE_START_AGENTS = [
    "pipeline_orchestrator_agent.md",
    "state_tracker_agent.md",
    "integrity_verification_agent.md",
]


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(SUITE_ROOT))
    except ValueError:
        return str(path)


def canonical_alias(alias: str | None) -> str | None:
    if not alias:
        return None
    return alias.lower().lstrip("/")


def command_by_alias(manifest: dict[str, Any], alias: str | None) -> dict[str, Any] | None:
    alias = canonical_alias(alias)
    if not alias:
        return None
    slash_alias = f"/{alias}"
    for command in manifest["commands"]:
        aliases = {item.lower() for item in command["aliases"]}
        if alias in aliases or slash_alias in aliases:
            return command
    return None


def find_alias(request: str) -> str | None:
    match = ALIAS_RE.search(request)
    if not match:
        return None
    return canonical_alias(match.group(1))


def is_vague_paper_topic(request: str) -> bool:
    lowered = request.lower()
    has_topic_signal = any(pattern.lower() in lowered for pattern in VAGUE_TOPIC_PATTERNS)
    has_clear_question = bool(QUESTION_RE.search(request)) and not bool(UNCLEAR_QUESTION_RE.search(request))
    explicit_skip = "skip scoping" in lowered or "do not ask" in lowered
    return has_topic_signal and not has_clear_question and not explicit_skip


def infer_natural_route(request: str) -> tuple[str, str, str]:
    lowered = request.lower()
    if is_vague_paper_topic(request):
        return "deep-research", "socratic", "paper_topic_scoping_override"
    if "reviewer" in lowered or "peer review" in lowered or "review this paper" in lowered:
        return "academic-paper-reviewer", "full", "natural_review_request"
    if "systematic review" in lowered or "meta-analysis" in lowered:
        return "deep-research", "systematic-review", "natural_research_request"
    if "literature review" in lowered or "annotated bibliography" in lowered:
        return "deep-research", "lit-review", "natural_research_request"
    if "academic pipeline" in lowered or "research to paper" in lowered or "full pipeline" in lowered:
        return "academic-pipeline", "pipeline", "natural_pipeline_request"
    return "academic-paper", "plan", "default_academic_planning"


def detect_checkpoint(request: str, workflow: str) -> str | None:
    if workflow != "academic-pipeline":
        return None
    lowered = request.lower()
    if "stop after" not in lowered and "checkpoint" not in lowered:
        return None
    if "dashboard" in lowered:
        return "pipeline_dashboard"
    if "stage 0" in lowered or "intake" in lowered:
        return "stage_0_intake"
    if "rq brief" in lowered or "research question" in lowered:
        return "stage_1_rq_brief"
    return "requested_checkpoint"


def profile_from_env(env: dict[str, str]) -> dict[str, Any]:
    full_runtime = env.get("ARS_CODEX_FULL_RUNTIME") == "1"
    agent_team = env.get("ARS_CODEX_AGENT_TEAM") == "1"
    hooks = env.get("ARS_CODEX_HOOKS") == "1"
    return {
        "full_runtime_enabled": full_runtime,
        "agent_team_enabled": full_runtime and agent_team,
        "hooks_enabled": full_runtime and hooks,
        "execution_mode": "codex_agent_team" if full_runtime and agent_team else "inline_role_prompts",
    }


def prompt_path(workflow: str, agent_file: str) -> str:
    return f"ars/{workflow}/agents/{agent_file}"


def build_agent_plan(manifest: dict[str, Any], workflow: str, mode: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    if not profile["agent_team_enabled"]:
        return []
    if workflow == "academic-paper-reviewer" and mode in {"full", "methodology-focus"}:
        plan: list[dict[str, Any]] = []
        for index, agent_file in enumerate(REVIEWER_ORDER):
            is_synth = agent_file == "editorial_synthesizer_agent.md"
            plan.append(
                {
                    "agent": agent_file.removesuffix(".md"),
                    "prompt_path": prompt_path(workflow, agent_file),
                    "dispatch": "after_independent_reviews" if is_synth else "parallel_independent_review",
                    "independence_group": "synthesis" if is_synth else "reviewer_blind_phase",
                    "output_contract": "synthesis_matrix" if is_synth else "independent_reviewer_section",
                    "order": index + 1,
                }
            )
        return plan
    if workflow == "academic-pipeline":
        return [
            {
                "agent": agent_file.removesuffix(".md"),
                "prompt_path": prompt_path(workflow, agent_file),
                "dispatch": "pipeline_start",
                "independence_group": "orchestration",
                "output_contract": "pipeline_checkpoint_record",
                "order": index + 1,
            }
            for index, agent_file in enumerate(PIPELINE_START_AGENTS)
        ]

    workflow_config = manifest["workflows"][workflow]
    return [
        {
            "agent": agent_file.removesuffix(".md"),
            "prompt_path": prompt_path(workflow, agent_file),
            "dispatch": "phase_role_prompt",
            "independence_group": workflow,
            "output_contract": "phase_artifact",
            "order": index + 1,
        }
        for index, agent_file in enumerate(workflow_config["agent_prompts"][:4])
    ]


def plan_request(request: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    manifest = load_manifest()
    profile = profile_from_env(env)
    alias = find_alias(request)
    command = command_by_alias(manifest, alias)
    route_reason = "alias_router" if command else "natural_language_router"

    if command:
        workflow = command["workflow"]
        mode = command["mode"]
        recipe = command["recipe"]
        model_hint = command["model_hint"]
        if canonical_alias(alias) in ALIAS_SOC_OVERRIDE and is_vague_paper_topic(request):
            workflow = "deep-research"
            mode = "socratic"
            route_reason = "paper_topic_scoping_override"
    else:
        workflow, mode, route_reason = infer_natural_route(request)
        recipe = None
        model_hint = None

    workflow_config = manifest["workflows"][workflow]
    checkpoint = detect_checkpoint(request, workflow)
    agent_plan = build_agent_plan(manifest, workflow, mode, profile)
    gates = [gate for gate in manifest["quality_gates"] if gate["kind"] in {"routing", "agent-team", "integrity", "material-passport"}]

    return {
        "adapter": manifest["adapter"]["name"],
        "profile": profile,
        "command_alias": alias,
        "command_recipe": recipe,
        "workflow": workflow,
        "mode": mode,
        "workflow_path": workflow_config["workflow_path"],
        "route_reason": route_reason,
        "model_hint": model_hint,
        "stop_at_checkpoint": checkpoint,
        "agent_template": workflow_config.get("agent_template"),
        "agent_team_plan": agent_plan,
        "quality_gates": gates,
        "degraded_behavior": [] if profile["full_runtime_enabled"] else ["full-runtime disabled; executing inline role prompts only"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="*", help="User request to route")
    parser.add_argument("--request-file", type=Path, help="Read request text from file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    if args.request_file:
        request = args.request_file.read_text(encoding="utf-8")
    else:
        request = " ".join(args.request)
    result = plan_request(request)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
