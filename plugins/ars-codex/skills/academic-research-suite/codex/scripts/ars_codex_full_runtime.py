#!/usr/bin/env python3
"""Codex full-runtime planner for the Academic Research Suite adapter.

The planner is intentionally deterministic and side-effect free. It does not
switch models, spawn agents, or execute hooks. It records model recommendations
and optional fixed-topology plans for a runtime that may delegate useful,
independent work natively.
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

ALIAS_RE = re.compile(r"^\s*(?:(?:use\s+)?\$academic-research-suite[\s.,:;]+)?(/?ars-[a-z0-9-]+)(?![\w-])", re.IGNORECASE)
DIRECT_MODE_RE = re.compile(r"^\s*\[direct-mode\]\s*", re.IGNORECASE)
SKILL_SELECTOR_RE = re.compile(r"^\s*(?:use\s+)?\$academic-research-suite[\s.,:;]+", re.IGNORECASE)
QUESTION_RE = re.compile(
    r"\b(research question|rq|hypothesis|hypotheses|pregunta de investigación|hipótesis)\b|研究問題|研究问题|假設|假设|연구 질문|연구 문제|가설",
    re.IGNORECASE,
)
UNCLEAR_QUESTION_RE = re.compile(
    r"(do not|don't|does not|doesn't|not yet|without|no)\s+.{0,40}\b(research question|rq|hypothesis|hypotheses)\b|"
    r"\bunclear\s+(research question|rq|hypothesis|hypotheses)\b|"
    r"\b(research question|rq|hypothesis|hypotheses)\b\s+.{0,30}\b(still\s+)?unclear\b|"
    r"尚未.{0,20}(研究問題|研究问题)|沒有.{0,20}(研究問題|研究问题)|没有.{0,20}(研究問題|研究问题)|"
    r"(아직|명확하지|모르겠).{0,30}(연구 질문|연구 문제|무엇을 연구)|"
    r"\b(?:sin|no tengo|no hay)\s+.{0,35}\bpregunta de investigación\b|"
    r"\bpregunta de investigación\b.{0,30}\b(?:no está clara|sin definir)\b",
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
    "题目是",
    "논문을 쓰고 싶",
    "논문 주제",
    "연구 방향",
    "무엇을 연구할지 모르겠",
    "quiero escribir un artículo sobre",
    "quiero redactar un artículo sobre",
    "tema de investigación",
)


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

TOPOLOGY_ARMS = {
    "inline-solo",
    "reviewer-two-plus-synthesis",
    "reviewer-five-panel",
    "reviewer-full-seven",
    "workflow-current",
}

REVIEWER_SEATS = [
    "eic_agent",
    "methodology_reviewer_agent",
    "domain_reviewer_agent",
    "perspective_reviewer_agent",
    "devils_advocate_reviewer_agent",
]

CROSS_MODEL_TRANSPORT_SELECTORS = frozenset({"", "api", "codex"})
CODEX_CITATION_TRANSPORT_FORBIDDEN_USES = [
    "devils_advocate",
    "reviewer_seat",
    "re_review_judge",
    "general_judgment",
]

# Require an action or a manuscript object: bare "review", "format", and
# output-format names also occur in research topics and confirmed criteria.
FORMAT_CONVERSION_REQUEST_RE = re.compile(
    r"(?:^|[.!?\n]\s*)(?:(?:please|can you|could you|help me(?: to)?|"
    r"i (?:want|would like) you to)\s+)?"
    r"(?:format[- ]convert\b|(?:convert|reformat|export)\b"
    r"(?=[^\n.!?]{0,160}\b(?:to|into|as)\s+(?:docx|pdf|latex|markdown|md|word)\b))|"
    r"(?:請|请|幫我|帮我|將|将|把)[^\n。！？]{0,80}"
    r"(?:論文|论文|稿件|文稿|手稿)[^\n。！？]{0,30}"
    r"(?:轉檔|转档|格式轉換|格式转换|轉換成|转换成|匯出成|导出为)",
    re.IGNORECASE,
)
MANUSCRIPT_REVIEW_REQUEST_RE = re.compile(
    r"\breview\s+(?:(?:this|the|my|our|attached|existing|submitted)\s+){0,3}"
    r"(?:paper|manuscript|article|draft)\b|"
    r"(?:論文|论文|稿件|手稿|文稿)(?:的)?(?:審查|审查|審稿|审稿|審閱|审阅)|"
    r"(?:審查|审查|審稿|审稿|審閱|审阅)[^\n。！？]{0,12}(?:論文|论文|稿件|手稿|文稿)",
    re.IGNORECASE,
)
REVIEW_COMPLETION_REQUEST_RE = re.compile(
    r"\b(?:complete|finish|conduct|perform|run|provide)\s+"
    r"(?:(?:the|a|an|this|my)\s+)?(?:full\s+)?(?:peer\s+)?review\b",
    re.IGNORECASE,
)

SCREENING_MODES = (
    "protocol", "quick", "pilot", "ta-screen", "ft-screen", "adjudicate", "audit", "report",
)
SCREENING_REQUEST_RE = re.compile(
    r"(?:^|[.!?\n]\s*)(?:(?:please|can you|could you|help me(?: to)?|"
    r"i (?:want|would like) you to)\s+)?(?:"
    r"(?:screen|rescreen)\s+(?:(?:these|the|my|our|pasted|exported|supplied|attached)\s+)*"
    r"(?:papers?|records?|abstracts?|titles?|exports?|studies|full[- ]texts?|pdfs?)\b|"
    r"(?:build|create|draft|prepare|turn)\b[^\n!?]{0,100}\bscreening protocol\b|"
    r"(?:pilot|resume|continue|run|perform|start)\s+"
    r"(?:(?:the|a|my|our|title[/ -]abstract|full[- ]text|study|record|calibration)\s+)*screening\b|"
    r"(?:adjudicate|resolve)\b[^\n.!?]{0,60}\bscreening conflicts\b|"
    r"(?:audit|recheck|double[- ]check)\s+(?:(?:my|the|these|our|screening)\s+)*exclusions\b|"
    r"(?:report|give|show|calculate)\b[^\n.!?]{0,100}"
    r"(?:\b(?:screening|selection) (?:counts|numbers)\b|\bfinished screening\b)|"
    r"(?:title[/ -]abstract|full[- ]text) screening\b|"
    r"is\s+(?:this|the)\s+abstract\s+eligible\b)|"
    r"(?:請|请|幫我|帮我)?(?:篩選|筛选)[^\n。！？]{0,35}"
    r"(?:文獻|文献|論文|论文|摘要|紀錄|记录|全文)|"
    r"(?:建立|制定|擬定|拟定)[^\n。！？]{0,30}(?:篩選|筛选)(?:方案|規則|规则|協定)|"
    r"(?:غربالگری کن|غربالگری مقالات|اسکرینینگ عنوان و چکیده)",
    re.IGNORECASE,
)


def infer_screening_mode(request: str) -> str | None:
    """Recognize requested selection work, never infer it from review materials.

    Protocol availability and all human gates are checked by the loaded workflow;
    selecting a mode does not attest that those prerequisites have been met.
    """
    # Negated stages must not become selected modes. Clause-level filtering
    # keeps a requested TA run when a later sentence postpones full text.
    clauses = re.split(r"(?<=[!?。！？;；,，])\s*|(?<=\.)\s+|\bbut\b", request, flags=re.IGNORECASE)
    request = "\n".join(clause for clause in clauses if not re.search(
        r"\b(?:do not|don't|never|not yet|not now)\b|\bnot\s+(?:full[- ]text|screening)\b|"
        r"不要|不需|不必|先別|先别", clause, re.IGNORECASE
    ))
    lowered = request.lower()
    named = re.match(r"^\s*(?:(?:use|run)\s+)?sr-screener\b", lowered)
    if not named and not SCREENING_REQUEST_RE.search(request):
        return None
    # Everyday screening/exclusion meanings do not name study selection.
    if not named and re.search(r"\b(?:plagiarism|airport passengers|financial ledger|spam|job applicants)\b", lowered):
        return None
    if named:
        leading_mode = re.match(r"\s+(" + "|".join(SCREENING_MODES) + r")(?![\w-])", lowered[named.end():])
        if leading_mode:
            return leading_mode.group(1)
        modes = [mode for mode in SCREENING_MODES if re.search(
            rf"(?<![\w-]){re.escape(mode)}(?![\w-])", lowered[named.end():]
        )]
        if len(modes) == 1:
            return modes[0]
    if re.search(r"\b(?:build|create|draft|prepare|turn)\b[^\n!?]{0,100}\bscreening protocol\b|(?:建立|制定|擬定|拟定).{0,30}(?:篩選|筛选)", lowered):
        return "protocol"
    if re.search(r"\b(?:adjudicate|resolve)\b.{0,60}\bscreening conflicts\b", lowered):
        return "adjudicate"
    if re.search(r"\b(?:audit|recheck|double[- ]check)\b.{0,40}\bexclusions\b", lowered):
        return "audit"
    if re.search(r"\b(?:report|give|show|calculate)\b.{0,100}(?:\b(?:screening|selection) (?:counts|numbers)\b|\bfinished screening\b)", lowered):
        return "report"
    if re.search(r"\bpilot\b", lowered):
        return "pilot"
    if re.search(r"\b(?:full[- ]text|pdfs?|ft-screen)\b|全文", lowered):
        return "ft-screen"
    if re.search(r"\b(?:quick|pasted)\b|\bis (?:this|the) abstract eligible\b", lowered):
        return "quick"
    # Numbered pasted records can identify a small triage request, not approval.
    if re.search(r"\bscreen these abstracts\b", lowered) and re.search(r"(?m)^\s*1[.)]\s+", request):
        return "quick"
    if named or re.search(r"proposal\.(?:docx|pdf)|no confirmed|without.{0,30}protocol|پروتکل", lowered):
        return "protocol"
    return "ta-screen"


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
    match = ALIAS_RE.match(request)
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
    if any(signal in lowered for signal in (
        "academic pipeline", "research to paper", "full pipeline", "full research-to-paper",
        "flujo de trabajo académico", "investigación a artículo",
        "pipeline de artículo completo", "flujo completo de investigación-publicación",
        "연구부터 논문까지", "논문 전체 워크플로", "完整研究到論文流程", "完整論文流程",
    )):
        return "academic-pipeline", "pipeline", "natural_pipeline_request"
    # Explicit modes retain their route even without the usual inputs (#889).
    if re.search(r"(?:檢查|核對|检查|核对)[^\n。？！]{0,40}(?:引用|參考文獻|参考文献|文獻|文献)|\b(?:check|verify|audit)\s+(?:(?:my|the|these|this)\s+)?(?:citations?|references?|refs)\b|\bcitation[- ]check\b|look over the refs|檢查引用|引用檢查|檢查參考文獻|核對文獻|检查引用|引用检查|检查参考文献|核对文献|인용 확인|인용 형식 검사", lowered):
        return "academic-paper", "citation-check", "natural_citation_request"
    if re.search(r"\b(?:write|draft)\s+(?:(?:an?|the|my|bilingual)\s+)*abstract\b|撰寫摘要|撰写摘要|寫摘要|写摘要", lowered):
        return "academic-paper", "abstract-only", "natural_abstract_request"
    if re.search(r"\b(?:revise|improve|polish)\s+(?:(?:this|the|my|our)\s+)*(?:paper|draft|manuscript|article)\b|修改論文|修訂論文|修改论文|修订论文", lowered):
        return "academic-paper", "revision", "natural_revision_request"
    if re.search(r"\b(?:revision roadmap|parse reviews|reviewer[- ]response coaching)\b|我收到審查意見|修訂路線圖", lowered):
        return "academic-paper", "revision-coach", "natural_revision_coach_request"
    if re.search(r"(?<![\w/-])(?:run\s+)?lit-review(?![\w-])", lowered):
        return "academic-paper", "lit-review", "natural_paper_literature_request"
    if re.search(r"\b(?:write|draft)\s+(?:(?:a|the|my|our)\s+)*literature review\b", lowered):
        return "academic-paper", "lit-review", "natural_paper_literature_request"
    if re.search(r"\b(?:draft|write|create)\s+(?:(?:a|an|the|my|paper)\s+)*outline\b|撰寫大綱|撰写大纲", lowered):
        return "academic-paper", "outline-only", "natural_outline_request"
    if re.search(r"\bplan\s+(?:(?:a|the|my|this)\s+)*(?:paper|manuscript)\b|論文規劃|论文规划", lowered):
        return "academic-paper", "plan", "natural_plan_request"
    screening_mode = infer_screening_mode(request)
    if screening_mode:
        return "sr-screener", screening_mode, "explicit_screening_request"
    # Spanish uses intent-specific compounds, preserving the upstream boundary
    # between editing one's draft and reviewing a submitted manuscript.
    if re.search(r"\b(?:enmendar|enmienda)\s+mi\s+artículo\b", lowered):
        return "academic-paper", "revision", "natural_revision_request"
    if any(signal in lowered for signal in (
        "analizar opiniones de revisores", "ruta de revisión",
        "recibí comentarios de revisores", "ayúdame con mi revisión",
    )):
        return "academic-paper", "revision-coach", "natural_revision_coach_request"
    if any(signal in lowered for signal in (
        "flujo de trabajo académico", "investigación a artículo",
        "pipeline de artículo completo", "flujo completo de investigación-publicación",
    )):
        return "academic-pipeline", "pipeline", "natural_pipeline_request"
    if any(signal in lowered for signal in ("guía mi investigación", "ayúdame a razonar")):
        return "deep-research", "socratic", "natural_socratic_request"
    if any(signal in lowered for signal in ("convertir a latex", "convertir formato")):
        return "academic-paper", "format-convert", "natural_format_conversion_request"
    if re.search(r"\b(?:revisar|revisa)\s+(?:este\s+|mi\s+|el\s+)?artículo\b", lowered) or any(
        signal in lowered for signal in ("revisión entre pares", "revisión de manuscrito", "revisión simulada")
    ):
        return "academic-paper-reviewer", "full", "natural_review_request"
    if "artículo de revisión bibliográfica" in lowered:
        return "academic-paper", "lit-review", "natural_paper_literature_request"
    if any(signal in lowered for signal in ("revisión sistemática", "metaanálisis")):
        return "deep-research", "systematic-review", "natural_research_request"
    if "revisión de literatura" in lowered:
        return "deep-research", "lit-review", "natural_research_request"
    if "verificar citas" in lowered:
        return "academic-paper", "citation-check", "natural_citation_request"
    if "escribir resumen" in lowered:
        return "academic-paper", "abstract-only", "natural_abstract_request"
    if FORMAT_CONVERSION_REQUEST_RE.search(request):
        return "academic-paper", "format-convert", "natural_format_conversion_request"
    if MANUSCRIPT_REVIEW_REQUEST_RE.search(request):
        return "academic-paper-reviewer", "full", "natural_review_request"
    # Research-review intents precede generic review completion. An explicit
    # request to review a manuscript above still wins over its study type.
    if any(signal in lowered for signal in ("systematic review", "meta-analysis", "體系性文獻回顧", "系統性文獻回顧", "系统性文献综述", "체계적 문헌고찰", "메타분석")):
        return "deep-research", "systematic-review", "natural_research_request"
    if any(signal in lowered for signal in ("literature review", "review of the literature", "review of literature", "annotated bibliography", "文獻回顧", "文献综述", "문헌 조사", "문헌 고찰")):
        return "deep-research", "lit-review", "natural_research_request"
    if any(
        signal in lowered
        for signal in (
            "simulate peer review",
            "peer review simulation",
            "논문을 심사",
            "논문 심사",
            "동료 심사",
            "원고 심사",
            "모의 심사",
            "심사자 관점",
        )
    ) or REVIEW_COMPLETION_REQUEST_RE.search(request):
        return "academic-paper-reviewer", "full", "natural_review_request"
    if any(signal in lowered for signal in ("academic pipeline", "research to paper", "full pipeline", "연구부터 논문까지", "논문 전체 워크플로")):
        return "academic-pipeline", "pipeline", "natural_pipeline_request"
    if any(signal in lowered for signal in ("논문을 수정", "논문 수정", "심사 의견 반영")):
        return "academic-paper", "revision", "natural_revision_request"
    if "초록 작성" in lowered:
        return "academic-paper", "abstract-only", "natural_abstract_request"
    if is_vague_paper_topic(request):
        return "deep-research", "socratic", "paper_topic_scoping_override"
    return "academic-paper", "plan", "default_academic_planning"



def intent_text(request: str) -> str:
    """Exclude quoted/fenced material and labeled artifact payloads from triggers.

    This is a conservative text planner, not a semantic injection detector. The
    calling session must still classify unlabeled third-party material as data.
    """
    lines = []
    fence = None
    for line in request.splitlines():
        if fence:
            if re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*", line):
                fence = None
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if opening:
            fence = opening.group(1)
        elif not re.match(r"^\s*>", line):
            lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r'"[^"\n]*"|“[^”]*”|「[^」]*」|『[^』]*』', "", text)
    text = re.split(
        r"(?im)^\s*(?:#{1,6}\s+|\*\*)?"
        r"(?:abstract(?: draft)?|full draft|literature collection|reviewer feedback|"
        r"manuscript text|摘要|全文|文獻清單|审稿意见|審查意見)\s*(?:\([^\n]*?\))?\s*[:：]",
        text,
        maxsplit=1,
    )[0]
    # Inline code names an artifact or an example, not a mode invocation.
    return re.sub(r"`[^`]*`", "", text)


def has_cross_phase_materials(request: str) -> bool:
    patterns = (
        r"\babstract(?: draft)?\b|摘要",
        r"\b(?:full draft|manuscript attached|draft attached|draft_v\d|draft[- ]v\d)\b|完整草稿|全文草稿",
        r"\b(?:collected.{0,35}papers|literature collection|literature review|bibliography|\d+\s+(?:papers|pdfs))\b|文獻清單|參考文獻|参考文献",
        r"\b(?:reviewer (?:comments|feedback)|decision letter)\b|審查意見|审稿意见",
    )
    return sum(bool(re.search(pattern, request, re.IGNORECASE)) for pattern in patterns) >= 2


def direct_target(request: str, manifest: dict[str, Any]) -> tuple[str, str | None] | None:
    """Resolve only a named workflow or an unambiguous named role after the token."""
    named_workflows = [name for name in manifest["workflows"] if re.search(
        rf"(?<![\w-]){re.escape(name)}(?![\w-])", request
    )]
    candidates = []
    for workflow, config in manifest["workflows"].items():
        if named_workflows and workflow not in named_workflows:
            continue
        for filename in config.get("agent_prompts", []):
            if re.search(rf"\b{re.escape(Path(filename).stem)}\b", request):
                candidates.append((workflow, filename))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates and len(named_workflows) == 1:
        return named_workflows[0], None
    return None


def clarification_plan(manifest, profile, request, reason, direct_mode):
    """No executable route or topology exists until the user settles intent."""
    return {
        "adapter": manifest["adapter"]["name"],
        "profile": profile,
        "routing_status": "clarification_required",
        "route_reason": reason,
        "dispatch_request": request,
        "direct_mode_honored": direct_mode,
        "direct_agent_path": None,
        "command_alias": None,
        "command_recipe": None,
        "workflow": None,
        "mode": None,
        "workflow_path": None,
        "required_read_paths": ["ars/shared/references/intent_clarification_protocol.md"],
        "required_read_status": "caller_must_read_before_execution",
        "model_hint": None,
        "model_plan": None,
        "stop_at_checkpoint": None,
        "agent_template": None,
        "agent_team_plan": [],
        "topology_plan": {
            "schema": "ars.codex.topology-plan.v1",
            "arm_id": None,
            "selection": {"source": "routing_clarification", "automatic": False},
            "applicable": False,
            "scope": "clarification_only",
            "nodes": [],
            "edges": [],
            "information_sharing": {},
            "execution_blocked": True,
            "reason_codes": [reason],
        },
        "quality_gates": [],
        "quality_gate_scope": "package_validation_catalog",
        "quality_gates_execute_on_request": False,
        "degraded_behavior": [],
    }

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
    requested_tiering = env.get("ARS_MODEL_TIERING", "").strip().lower()
    requested_cross_model = env.get("ARS_CROSS_MODEL", "").strip()
    raw_cross_model_transport = env.get("ARS_CROSS_MODEL_TRANSPORT", "")
    if raw_cross_model_transport not in CROSS_MODEL_TRANSPORT_SELECTORS:
        raise ValueError(
            "invalid ARS_CROSS_MODEL_TRANSPORT selector; expected the variable to be "
            "absent, or set to api or codex "
            "and refused to fall through to another transport"
        )
    cross_model_transport_selector = raw_cross_model_transport or "unset"
    cross_model_effective_transport = (
        "codex" if cross_model_transport_selector == "codex" else "api"
    )
    cross_model_transport_ready = not (
        cross_model_effective_transport == "codex" and not requested_cross_model
    )
    raw_stale_days = env.get("ARS_CACHE_STALE_ADVISORY_DAYS")
    try:
        cache_stale_advisory_days = 30 if raw_stale_days is None else int(raw_stale_days)
    except ValueError:
        cache_stale_advisory_days = 30
    if cache_stale_advisory_days < 0:
        cache_stale_advisory_days = 30
    cache_revalidation_requested = env.get("ARS_CACHE_REVALIDATE") == "1"
    topology_experiment = env.get("ARS_CODEX_TOPOLOGY_EXPERIMENT") == "1"
    requested_topology_arm = env.get("ARS_CODEX_TOPOLOGY_ARM", "").strip() or None
    if not requested_tiering:
        tiering_status = "unset"
    elif requested_tiering not in {"economy", "quality-boost"}:
        tiering_status = "unknown_warn_unset"
    elif not (full_runtime and agent_team):
        tiering_status = "inline_noop"
    else:
        tiering_status = "advisory_requires_runtime_model_override"
    if cross_model_effective_transport == "codex" and not cross_model_transport_ready:
        cross_model_status = "codex_transport_unavailable_missing_ARS_CROSS_MODEL"
        cross_model_scope = "none"
    elif cross_model_effective_transport == "codex":
        cross_model_status = "codex_citation_only_requires_explicit_request_and_consent"
        cross_model_scope = "citation_integrity_only"
    elif not requested_cross_model:
        cross_model_status = "unset"
        cross_model_scope = "none"
    elif full_runtime and agent_team:
        cross_model_status = "dispatcher_transport_requires_explicit_request_and_consent"
        cross_model_scope = "api_cross_model_workflows"
    else:
        cross_model_status = "inline_transport_requires_explicit_request_and_consent"
        cross_model_scope = "api_cross_model_workflows"
    return {
        "full_runtime_enabled": full_runtime,
        "agent_team_enabled": full_runtime and agent_team,
        "hooks_enabled": full_runtime and hooks,
        "execution_mode": "codex_agent_team" if full_runtime and agent_team else "native_adaptive",
        "native_delegation_policy": "useful_independent_subtasks_when_runtime_available",
        "native_delegation_fallback": "inline_role_prompts",
        "fixed_topology_opt_in": full_runtime and agent_team,
        "model_tiering_requested": requested_tiering or None,
        "model_tiering_status": tiering_status,
        "cross_model_configured": requested_cross_model or None,
        "cross_model_transport_selector": cross_model_transport_selector,
        "cross_model_effective_transport": cross_model_effective_transport,
        "cross_model_transport_ready": cross_model_transport_ready,
        "cross_model_transport_scope": cross_model_scope,
        "cross_model_explicit_consent_required": bool(requested_cross_model)
        or cross_model_effective_transport == "codex",
        "cross_model_forbidden_uses": (
            CODEX_CITATION_TRANSPORT_FORBIDDEN_USES
            if cross_model_effective_transport == "codex"
            else []
        ),
        "cross_model_handoff_status": cross_model_status,
        "cache_stale_advisory_days": cache_stale_advisory_days,
        "cache_revalidation_requested": cache_revalidation_requested,
        "cache_revalidation_status": (
            "live_bibliographic_revalidation_requested"
            if cache_revalidation_requested
            else "cached_default"
        ),
        "topology_experiment_enabled": topology_experiment,
        "topology_arm_requested": requested_topology_arm,
        "topology_arm_status": (
            "explicit_experiment"
            if topology_experiment and requested_topology_arm
            else "missing_arm_blocked"
            if topology_experiment
            else "ignored_without_experiment_opt_in"
            if requested_topology_arm
            else "unset"
        ),
    }


def build_model_plan(
    manifest: dict[str, Any],
    workflow: str,
    mode: str,
    env: dict[str, str],
) -> dict[str, Any]:
    """Plan a future selection; never infer what model actually executed."""
    policy = manifest["runtime_options"]["model_policy"]
    requested_model = env.get("ARS_CODEX_MODEL", "").strip() or None
    requested_effort = env.get("ARS_CODEX_REASONING_EFFORT", "").strip() or None
    target_model = requested_model or policy["preferred_model"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}", target_model):
        raise ValueError("invalid ARS_CODEX_MODEL: expected a model identifier")
    known_model = target_model == policy["preferred_model"]
    supported = policy["codex_supported_reasoning_efforts"] if known_model else []
    if requested_effort and requested_effort not in policy["codex_supported_reasoning_efforts"]:
        raise ValueError("unsupported ARS_CODEX_REASONING_EFFORT for this Codex model policy")
    if requested_effort and not known_model:
        raise ValueError(
            "cannot verify ARS_CODEX_REASONING_EFFORT for the overridden model; "
            "omit the effort and use that runtime's model catalog"
        )

    routine_modes = policy["routine_modes"].get(workflow, [])
    complexity = "routine" if mode in routine_modes else "judgment_or_complex_research"
    effort = requested_effort or (
        policy["reasoning_defaults"][complexity] if known_model else None
    )
    observed_model = env.get("ARS_CODEX_ACTIVE_MODEL", "").strip() or None
    observed_effort = env.get("ARS_CODEX_ACTIVE_REASONING_EFFORT", "").strip() or None
    argv = ["codex", "--model", target_model]
    if effort:
        argv.extend(["-c", f'model_reasoning_effort="{effort}"'])
    return {
        "schema": "ars.codex.model-plan.v1",
        "preferred_model": policy["preferred_model"],
        "requested_model": requested_model,
        "requested_reasoning_effort": requested_effort,
        "target_model": target_model,
        "target_reasoning_effort": effort,
        "selection_source": "explicit_model_override" if requested_model else "repository_quality_policy",
        "effort_source": (
            "explicit_effort_override" if requested_effort
            else "repository_quality_policy" if known_model
            else "unresolved_model_default"
        ),
        "task_class": complexity,
        "supported_reasoning_efforts": supported,
        "capability_evidence": policy["capability_evidence"] if known_model else None,
        "quality_policy_evidence": "repository_policy_not_measured_optimum",
        "project_default_reference": policy["project_default_reference"],
        "application_status": "planned_only_current_session_unchanged",
        "current_runtime_observation": {
            "model": observed_model,
            "reasoning_effort": observed_effort,
            "source": "caller_reported" if observed_model or observed_effort else "unobserved",
            "independently_verified": False,
        },
        "launch_argv": argv,
        "launch_executed": False,
        "api_effort_mapping": "none_codex_values_are_not_api_authority",
        "runtime_selection_required": True,
    }


def prompt_path(workflow: str, agent_file: str) -> str:
    return f"ars/{workflow}/agents/{agent_file}"


def _node(
    workflow: str,
    node_id: str,
    agent_file: str | None,
    phase: str,
    depends_on: list[str],
    reads: list[str],
    emits: list[str],
) -> dict[str, Any]:
    return {
        "id": node_id,
        "agent": agent_file.removesuffix(".md") if agent_file else node_id,
        "prompt_path": prompt_path(workflow, agent_file) if agent_file else None,
        "phase": phase,
        "depends_on": depends_on,
        "reads": reads,
        "emits": emits,
    }


def _reviewer_topology(arm_id: str) -> tuple[list[dict[str, Any]], str]:
    frozen = ["input_bundle", "frozen_reviewer_configuration"]
    if arm_id == "reviewer-two-plus-synthesis":
        seats = ["methodology_reviewer_agent", "domain_reviewer_agent"]
        nodes = [
            _node(
                "academic-paper-reviewer",
                seat,
                f"{seat}.md",
                "blind_review",
                [],
                frozen,
                [f"{seat}_report"],
            )
            for seat in seats
        ]
    elif arm_id == "reviewer-five-panel":
        seats = REVIEWER_SEATS
        nodes = [
            _node(
                "academic-paper-reviewer",
                seat,
                f"{seat}.md",
                "blind_review",
                [],
                frozen,
                [f"{seat}_report"],
            )
            for seat in seats
        ]
    elif arm_id == "reviewer-full-seven":
        field_id = "field_analyst_agent"
        field = _node(
            "academic-paper-reviewer",
            field_id,
            "field_analyst_agent.md",
            "configuration",
            [],
            ["input_bundle"],
            ["reviewer_configuration"],
        )
        seats = REVIEWER_SEATS
        nodes = [field]
        nodes.extend(
            _node(
                "academic-paper-reviewer",
                seat,
                f"{seat}.md",
                "blind_review",
                [field_id],
                ["input_bundle", "reviewer_configuration"],
                [f"{seat}_report"],
            )
            for seat in seats
        )
    else:
        raise ValueError(f"unsupported reviewer topology arm: {arm_id}")

    reviewer_ids = [node["id"] for node in nodes if node["phase"] == "blind_review"]
    synth_dependencies = list(reviewer_ids)
    if arm_id == "reviewer-full-seven":
        synth_dependencies.insert(0, "field_analyst_agent")
    synth_reads = ["input_bundle", "reviewer_configuration"] + [
        f"{seat}_report" for seat in reviewer_ids
    ]
    nodes.append(
        _node(
            "academic-paper-reviewer",
            "editorial_synthesizer_agent",
            "editorial_synthesizer_agent.md",
            "synthesis",
            synth_dependencies,
            synth_reads,
            ["editorial_synthesis"],
        )
    )
    return nodes, "complete_review"


def _workflow_topology(workflow: str) -> tuple[list[dict[str, Any]], str]:
    if workflow != "academic-pipeline":
        return [], "unavailable"
    orchestrator = _node(
        workflow,
        "pipeline_orchestrator_agent",
        "pipeline_orchestrator_agent.md",
        "startup",
        [],
        ["input_bundle", "material_passport"],
        ["dispatch_plan"],
    )
    tracker = _node(
        workflow,
        "state_tracker_agent",
        "state_tracker_agent.md",
        "meta_state",
        ["pipeline_orchestrator_agent"],
        ["dispatch_plan", "material_passport"],
        ["pipeline_state"],
    )
    integrity = _node(
        workflow,
        "integrity_verification_agent",
        "integrity_verification_agent.md",
        "checkpoint_2_5_or_4_5",
        ["pipeline_orchestrator_agent"],
        ["dispatch_plan", "input_bundle", "material_passport"],
        ["integrity_report"],
    )
    return [orchestrator, tracker, integrity], "declared_runtime_roles"


def validate_topology_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes = plan.get("nodes", [])
    ids = [node.get("id") for node in nodes]
    if len(ids) != len(set(ids)):
        errors.append("topology_duplicate_node_id")
    id_set = set(ids)
    for node in nodes:
        for parent in node.get("depends_on", []):
            if parent not in id_set:
                errors.append("topology_parent_missing")
    visiting: set[str] = set()
    visited: set[str] = set()

    by_id = {node["id"]: node for node in nodes if node.get("id")}

    def visit(node_id: str) -> None:
        if node_id in visiting:
            errors.append("topology_cycle")
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for parent in by_id.get(node_id, {}).get("depends_on", []):
            if parent in by_id:
                visit(parent)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in by_id:
        visit(node_id)

    if plan.get("information_sharing", {}).get("peer_outputs") == "hidden_until_synthesis":
        review_reports = {f"{seat}_report" for seat in REVIEWER_SEATS}
        for node in nodes:
            if node.get("phase") == "blind_review" and review_reports.intersection(node.get("reads", [])):
                errors.append("topology_blind_reviewer_reads_peer_output")
    return sorted(set(errors))


def build_topology_plan(
    workflow: str,
    mode: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    experiment = profile["topology_experiment_enabled"]
    requested = profile["topology_arm_requested"] if experiment else None
    selection_source = "explicit_experiment" if experiment else "explicit_runtime" if profile["agent_team_enabled"] else "default_inline"
    arm_id = requested or (
        "reviewer-full-seven"
        if profile["agent_team_enabled"] and workflow == "academic-paper-reviewer" and mode == "full"
        else "workflow-current"
        if profile["agent_team_enabled"] and workflow == "academic-pipeline"
        else "inline-solo"
    )
    errors: list[str] = []
    applicable = True
    if experiment and requested is None:
        errors.append("topology_arm_required")
    elif arm_id not in TOPOLOGY_ARMS:
        errors.append("topology_arm_unknown")
    reviewer_arms = {
        "reviewer-two-plus-synthesis",
        "reviewer-five-panel",
        "reviewer-full-seven",
    }
    if arm_id in reviewer_arms and workflow != "academic-paper-reviewer":
        errors.append("topology_arm_not_applicable")
        applicable = False
    if arm_id == "workflow-current" and workflow != "academic-pipeline":
        errors.append("topology_arm_not_applicable")
        applicable = False
    if arm_id != "inline-solo" and not profile["agent_team_enabled"]:
        errors.append("topology_agent_team_runtime_required")

    nodes: list[dict[str, Any]] = []
    scope = "complete_inline"
    information_sharing = {
        "policy": "single_context",
        "peer_outputs": "not_applicable",
        "memory_scope": "off",
        "initial_input": "caller_supplied_digest_required_for_experiment",
    }
    if not errors:
        if arm_id == "inline-solo":
            nodes = [
                _node(
                    workflow,
                    "inline_owner",
                    None,
                    "inline",
                    [],
                    ["input_bundle"],
                    ["workflow_result"],
                )
            ]
        elif arm_id in reviewer_arms:
            nodes, scope = _reviewer_topology(arm_id)
            information_sharing = {
                "policy": "edge_allowlist",
                "peer_outputs": "hidden_until_synthesis",
                "memory_scope": "role_scoped",
                "initial_input": "same_digest",
            }
        elif arm_id == "workflow-current":
            nodes, scope = _workflow_topology(workflow)
            information_sharing = {
                "policy": "edge_allowlist",
                "peer_outputs": "workflow_dependencies_only",
                "memory_scope": "role_scoped",
                "initial_input": "same_digest",
            }

    plan = {
        "schema": "ars.codex.topology-plan.v1",
        "arm_id": arm_id,
        "selection": {"source": selection_source, "automatic": False},
        "applicable": applicable,
        "scope": scope,
        "nodes": nodes,
        "edges": [
            {
                "from": parent,
                "to": node["id"],
                "artifacts": sorted(
                    set(next(item for item in nodes if item["id"] == parent)["emits"])
                    .intersection(node["reads"])
                ),
            }
            for node in nodes
            for parent in node["depends_on"]
        ],
        "information_sharing": information_sharing,
        "execution_blocked": bool(errors),
        "reason_codes": errors,
    }
    if not errors:
        plan["reason_codes"] = validate_topology_plan(plan)
        plan["execution_blocked"] = bool(plan["reason_codes"])
    return plan


def agent_plan_from_topology(topology: dict[str, Any]) -> list[dict[str, Any]]:
    if topology["execution_blocked"] or topology["arm_id"] == "inline-solo":
        return []
    plan: list[dict[str, Any]] = []
    for index, node in enumerate(topology["nodes"]):
        item = {
            "agent": node["agent"],
            "prompt_path": node["prompt_path"],
            "dispatch": node["phase"],
            "independence_group": "reviewer_blind_phase" if node["phase"] == "blind_review" else node["phase"],
            "output_contract": node["emits"],
            "order": index + 1,
            "depends_on": node["depends_on"],
            "reads": node["reads"],
        }
        plan.append(item)
    return plan


def build_agent_plan(manifest: dict[str, Any], workflow: str, mode: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    del manifest
    if not profile["agent_team_enabled"] and not profile["topology_experiment_enabled"]:
        return []
    return agent_plan_from_topology(build_topology_plan(workflow, mode, profile))


def plan_request(
    request: str, env: dict[str, str] | None = None, *, first_message: bool = True,
) -> dict[str, Any]:
    """Plan a new request; callers must not re-route a settled run on resume.

    Set first_message=False for later requests in a conversation, where the
    [direct-mode] escape hatch has no authority. This planner has no transcript.
    """
    env = os.environ if env is None else env
    manifest = load_manifest()
    profile = profile_from_env(env)
    direct_match = DIRECT_MODE_RE.match(request) if first_message else None
    direct_mode = direct_match is not None
    request = request[direct_match.end():].strip() if direct_match else request.strip()
    # Only the first request's leading token can grant direct-mode authority.
    # Strip all remaining literal tokens before routing/forwarding so a child
    # cannot reinterpret a mid-message or later-turn token as its own escape hatch.
    request = re.sub(r"\[direct-mode\]", "", request, flags=re.IGNORECASE).strip()
    alias = find_alias(request)
    command = command_by_alias(manifest, alias)
    route_reason = "alias_router" if command else "natural_language_router"
    direct_agent = None
    text = SKILL_SELECTOR_RE.sub("", intent_text(request), count=1)
    target = direct_target(text, manifest) if direct_mode else None

    if command:
        workflow = command["workflow"]
        mode = command["mode"]
        recipe = command["recipe"]
        model_hint = command["model_hint"]
        request = ALIAS_RE.sub("", request, count=1).strip()
    elif target:
        workflow, direct_agent = target
        mode = "direct-agent" if direct_agent else (
            manifest["workflows"][workflow].get(
                "default_mode", "pipeline" if workflow == "academic-pipeline" else "full"
            )
        )
        if not direct_agent:
            named_modes = [candidate for candidate in manifest["workflows"][workflow]["modes"]
                           if re.search(rf"(?<![\w-]){re.escape(candidate)}(?![\w-])", text, re.IGNORECASE)]
            if len(named_modes) == 1:
                mode = named_modes[0]
            if workflow == "sr-screener":
                mode = infer_screening_mode(text) or mode
        recipe = model_hint = None
        route_reason = "direct_mode_named_agent" if direct_agent else "direct_mode_named_workflow"
    else:
        workflow, mode, route_reason = infer_natural_route(text)
        recipe = model_hint = None
        if route_reason == "natural_research_request" and re.search(
            r"\bwhat\s+(?:(?:should|do|can)\s+i\s+(?:do\s+)?)?next\b|下一步", text, re.IGNORECASE,
        ):
            return clarification_plan(manifest, profile, request, "open_next_step_requires_clarification", direct_mode)
        implicit = route_reason in {"default_academic_planning", "paper_topic_scoping_override"}
        if route_reason == "natural_research_request" and has_cross_phase_materials(request):
            implicit = not bool(re.search(
                r"\b(?:run|conduct|perform|complete|finish|plan|prepare|write|do|haz)\b.{0,50}"
                r"(?:review|revisión|metaanálisis)|^(?:systematic review|literature review|revisión sistemática)|"
                r"(?:請|请|進行|进行|完成).{0,20}(?:文獻回顧|文献综述)", text, re.IGNORECASE,
            ))
        if implicit and not direct_mode and has_cross_phase_materials(request):
            return clarification_plan(manifest, profile, request, "cross_phase_materials_require_clarification", direct_mode)
        if implicit and (direct_mode or not (
            is_vague_paper_topic(text) or QUESTION_RE.search(text)
            or re.search(r"\b(?:plan|outline|preview|write)\b.{0,35}\b(?:paper|article|outline)\b|論文規劃|论文规划|quiero escribir un artículo", text, re.IGNORECASE)
        )):
            return clarification_plan(manifest, profile, request, "ambiguous_intent_requires_clarification", direct_mode)

    workflow_config = manifest["workflows"][workflow]
    model_plan = build_model_plan(manifest, workflow, mode, env)
    checkpoint = detect_checkpoint(request, workflow)
    topology_profile = profile
    if direct_agent:
        # A named role must not widen into the containing workflow's whole team.
        topology_profile = {**profile, "agent_team_enabled": False, "topology_experiment_enabled": False}
    topology_plan = build_topology_plan(workflow, mode, topology_profile)
    if workflow == "sr-screener" and not direct_agent:
        # This static topology plans the dispatcher only. It cannot certify
        # human gates, assign unknown batches, or promise isolated reviewers.
        topology_plan["scope"] = "screening_dispatcher_only"
        topology_plan["information_sharing"]["policy"] = "dispatcher_only_no_dual_review"
        for node in topology_plan["nodes"]:
            node["emits"] = ["screening_dispatch_plan"]
    if direct_agent:
        topology_plan["scope"] = "direct_agent_only"
        node = topology_plan["nodes"][0]
        node.update({"agent": Path(direct_agent).stem,
                     "prompt_path": prompt_path(workflow, direct_agent),
                     "emits": ["direct_agent_result"]})
    if profile["agent_team_enabled"] or profile["topology_experiment_enabled"]:
        agent_plan = agent_plan_from_topology(topology_plan)
    else:
        agent_plan = []
    for item in agent_plan:
        role_effort = model_plan["target_reasoning_effort"]
        model_policy = manifest["runtime_options"]["model_policy"]
        if (
            model_plan["requested_reasoning_effort"] is None
            and model_plan["target_model"] == model_policy["preferred_model"]
            and item["agent"] in model_policy["routine_agents"]
        ):
            role_effort = model_policy["reasoning_defaults"]["routine"]
        item["model_selection"] = {
            "model": model_plan["target_model"],
            "reasoning_effort": role_effort,
            "status": "planned_requires_runtime_model_override",
            "observed_model": None,
            "fallback": "inherit_active_model_and_record_actual_execution",
        }
        if item["agent"] == "domain_reviewer_agent":
            if profile["cross_model_effective_transport"] == "codex":
                item["cross_model_reviewer_track"] = (
                    "excluded_codex_transport_is_citation_only"
                )
            elif profile["cross_model_configured"]:
                item["cross_model_reviewer_track"] = (
                    "configured_requires_explicit_content_consent"
                )
            else:
                item["cross_model_reviewer_track"] = (
                    "not_configured_single_family_disclosure_required"
                )
    gates = [gate for gate in manifest["quality_gates"] if gate["kind"] in {"routing", "agent-team", "integrity", "material-passport"}]

    required_reads = [workflow_config["workflow_path"]]
    if recipe:
        required_reads.insert(0, recipe)
    if direct_agent:
        required_reads.append(prompt_path(workflow, direct_agent))
    if workflow == "academic-paper" and mode == "citation-check":
        required_reads.append("ars/academic-paper/agents/citation_compliance_agent.md")
        if re.search(r"Chinese|中文|漢字|汉字|중국어", request, re.IGNORECASE):
            required_reads.append("ars/academic-paper/references/apa7_chinese_citation_guide.md")
    screening_contract = None
    if workflow == "sr-screener":
        required_reads.extend([
            workflow_config["agent_template"],
            "ars/sr-screener/references/orchestration.md",
            "ars/sr-screener/references/decision_rules.md",
        ])
        role_file = {
            "protocol": "protocol_architect_agent.md",
            "pilot": "qc_auditor_agent.md",
            "report": "reporter_agent.md",
        }.get(mode, "screening_reviewer_agent.md")
        required_reads.append(prompt_path(workflow, role_file))
        if mode != "protocol":
            required_reads.append("ars/sr-screener/references/reviewer_roles.md")
        screening_contract = {
            **manifest["runtime_options"]["screening"],
            "gate_status": "not_attested_by_planner",
            "dispatch_authorized": False,
        }

    return {
        "adapter": manifest["adapter"]["name"],
        "profile": profile,
        "routing_status": "routed",
        "dispatch_request": request,
        "direct_mode_honored": direct_mode,
        "direct_agent_path": prompt_path(workflow, direct_agent) if direct_agent else None,
        "required_read_paths": required_reads,
        "required_read_status": "caller_must_read_before_execution",
        "command_alias": alias,
        "command_recipe": recipe,
        "workflow": workflow,
        "mode": mode,
        "workflow_path": workflow_config["workflow_path"],
        "route_reason": route_reason,
        "model_hint": model_hint,
        "model_plan": model_plan,
        "stop_at_checkpoint": checkpoint,
        "agent_template": None if direct_agent else workflow_config.get("agent_template"),
        "agent_team_plan": agent_plan,
        "screening_contract": screening_contract,
        "topology_plan": topology_plan,
        "quality_gates": gates,
        "quality_gate_scope": "package_validation_catalog",
        "quality_gates_execute_on_request": False,
        "degraded_behavior": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="*", help="User request to route")
    parser.add_argument("--request-file", type=Path, help="Read request text from file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--not-first-message", action="store_true", help="Disable the first-message-only direct-mode escape hatch")
    args = parser.parse_args()

    if args.request_file:
        request = args.request_file.read_text(encoding="utf-8")
    else:
        request = " ".join(args.request)
    try:
        result = plan_request(request, first_message=not args.not_first_message)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
