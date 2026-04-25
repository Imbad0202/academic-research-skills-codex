---
name: academic-research-suite
description: >
  Codex-native Academic Research Skills suite for deep research, academic paper
  writing, manuscript review, full research-to-paper pipelines, and experiment
  planning or validation. Use when the user asks for deep research, literature
  review, systematic review, meta-analysis, research question refinement,
  academic paper drafting, paper revision, citation or integrity checks,
  reviewer simulation, peer review, editorial decision letters, research-to-paper
  workflows, experiment execution planning, statistical interpretation, or human
  study protocol support. This skill vendors ARS role prompts, references,
  templates, and shared handoff schemas under ars/.
metadata:
  version: "0.1.0"
  upstream_suite: "academic-research-skills"
  codex_adapter: true
---

# Academic Research Suite for Codex

This is a Codex adapter for the ARS suite. The vendored ARS content lives under
`ars/`; keep it as source material and route through this file first.

## First Rule

Do not load the whole suite by default. Select one workflow, read that workflow's
`SKILL.md`, then load only the agent, reference, template, or shared files needed
for the user's current stage.

## Workflow Router

Choose the workflow by intent:

| User intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact-checking, research question refinement | `ars/deep-research/SKILL.md` |
| Academic paper writing, paper outline, abstract, revision, citation formatting, AI disclosure, LaTeX/DOCX/PDF formatting guidance | `ars/academic-paper/SKILL.md` |
| Paper review, peer review simulation, editorial decision, reviewer calibration, re-review after revision | `ars/academic-paper-reviewer/SKILL.md` |
| End-to-end research-to-paper pipeline, integrity gate, staged review/revision/finalization workflow | `ars/academic-pipeline/SKILL.md` |
| Experiment planning, code experiment execution plan, human study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/SKILL.md` |

If the request spans multiple workflows, start with `ars/academic-pipeline/SKILL.md`
unless the user clearly asked for a single phase.

## Codex Runtime Mapping

The upstream ARS files were written for Claude Code. Apply these mappings when
using them in Codex:

| Upstream wording | Codex behavior |
|---|---|
| Agent Team, agent, dispatch, handoff | Read the referenced `agents/*.md` file as a role or phase prompt and perform that phase inline. |
| Agent tool, Task tool, subagent | Do not spawn agents automatically. Only use Codex subagents when the user explicitly asks for delegation or parallel agents. |
| AskUserQuestion | Ask concise clarification questions, or use Codex's structured user-input tool when available in the active mode. |
| WebSearch | Use Codex web browsing for current facts, source verification, citation checks, and external evidence. Provide source links. |
| Bash, Write, Edit | Treat as capability descriptions, not required tool names. Follow Codex safety rules and the user's filesystem constraints. |
| Claude, Claude Code, model-specific wording | Interpret as "the current Codex agent" unless the text is part of a disclosure template or historical example. |
| `ARS_CROSS_MODEL` | Disabled by default in Codex. Mention it as an optional upstream feature, but do not call external model APIs unless the user explicitly asks. |

## Agent Prompt Use

When a workflow lists agents:

1. Read the workflow `SKILL.md` to identify the mode and phase.
2. Read the specific `agents/<name>.md` files for the current phase.
3. Treat each agent file as a scoped role prompt with an input/output contract.
4. Produce the phase output in the current conversation unless the user requested files.
5. Use `ars/shared/handoff_schemas.md` when a phase hands material to another phase.

For multi-review phases, preserve independence by writing each reviewer section
before synthesizing. Do not let the final synthesis erase critical findings from
devil's advocate or methodology roles.

## Canonical Agent Files

Use these exact filenames. Do not invent hyphenated alternatives or rename files
from memory.

`ars/deep-research/agents/`:
`bibliography_agent.md`, `devils_advocate_agent.md`,
`editor_in_chief_agent.md`, `ethics_review_agent.md`,
`meta_analysis_agent.md`, `monitoring_agent.md`,
`report_compiler_agent.md`, `research_architect_agent.md`,
`research_question_agent.md`, `risk_of_bias_agent.md`,
`socratic_mentor_agent.md`, `source_verification_agent.md`,
`synthesis_agent.md`.

`ars/academic-paper/agents/`:
`abstract_bilingual_agent.md`, `argument_builder_agent.md`,
`citation_compliance_agent.md`, `draft_writer_agent.md`,
`formatter_agent.md`, `intake_agent.md`,
`literature_strategist_agent.md`, `peer_reviewer_agent.md`,
`revision_coach_agent.md`, `socratic_mentor_agent.md`,
`structure_architect_agent.md`, `visualization_agent.md`.

`ars/academic-paper-reviewer/agents/`:
`devils_advocate_reviewer_agent.md`, `domain_reviewer_agent.md`,
`editorial_synthesizer_agent.md`, `eic_agent.md`,
`field_analyst_agent.md`, `methodology_reviewer_agent.md`,
`perspective_reviewer_agent.md`.

`ars/academic-pipeline/agents/`:
`collaboration_depth_agent.md`, `integrity_verification_agent.md`,
`pipeline_orchestrator_agent.md`, `state_tracker_agent.md`.

`ars/experiment-agent/agents/`:
`code_runner_agent.md`, `study_manager_agent.md`.

## Shared Resources

Use `ars/shared/` for cross-workflow contracts and quality gates:

- `ars/shared/handoff_schemas.md` defines inter-stage artifact schemas.
- `ars/shared/style_calibration_protocol.md` defines writing voice calibration.
- `ars/shared/mode_spectrum.md` defines fidelity, balanced, and originality modes.
- `ars/shared/agents/compliance_agent.md` defines compliance checks.
- `ars/shared/compliance_checkpoint_protocol.md`, `ars/shared/prisma_trAIce_protocol.md`, and `ars/shared/raise_framework.md` define integrity and reporting gates.
- `ars/scripts/` contains upstream validators and reference adapters.
- `ars/examples/` contains upstream non-PDF fixtures and templates.
- `ars/docs/design/` contains upstream design specs referenced by ARS protocols.

When an ARS file points to `shared/...`, resolve it as `ars/shared/...`.
When it points to another workflow, resolve it under `ars/<workflow>/...`.
When it points to root-level `scripts/...`, `examples/...`, or `docs/...`, resolve
it under `ars/scripts/...`, `ars/examples/...`, or `ars/docs/...`.

## Verification Discipline

For claims, citations, references, statistics, journal policies, API behavior, and
current facts, verify against primary or authoritative sources. If verification is
not possible, mark the item as unverified instead of inventing support.

Never fabricate references. For citation existence checks, prefer DOI or official
metadata lookup, then authoritative web search. Semantic Scholar API instructions
are in `ars/deep-research/references/semantic_scholar_api_protocol.md`; use them
only when the task needs programmatic reference verification.

## Output Defaults

- Default language follows the user's language.
- For Chinese, use Traditional Chinese unless the user requests otherwise.
- For staged workflows, show the current stage, required inputs, output artifact,
  and whether the next gate is optional or mandatory.
- For paper/research outputs, keep uncertainty explicit and separate evidence,
  inference, and recommendation.
