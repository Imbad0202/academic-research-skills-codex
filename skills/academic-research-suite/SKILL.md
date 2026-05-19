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
  study protocol support. Also use for Claude-style ARS command aliases such as
  /ars-plan, ars-plan, /ars-outline, /ars-abstract, /ars-lit-review,
  /ars-citation-check, /ars-disclosure, /ars-format-convert,
  /ars-revision-coach, /ars-revision, and /ars-full. This skill vendors ARS
  role prompts, references, templates, and shared handoff schemas under ars/.
metadata:
  version: "0.1.8"
  upstream_suite: "academic-research-skills"
  codex_adapter: true
---

# Academic Research Suite for Codex

This is a Codex adapter for the ARS suite. The vendored ARS content lives under
`ars/`; keep it as source material and route through this file first.

## Versioning

This Codex package is version `0.1.8`. The repo-root `VERSION`, this
`SKILL.md` metadata version, and `manifest.json` `adapter_version` must match.
Vendored ARS suite versions are tracked separately by source repository commit
in `manifest.json`.

## First Rule

Do not load the whole suite by default. Select one workflow, read that workflow's
`WORKFLOW.md`, then load only the agent, reference, template, or shared files needed
for the user's current stage.

The internal workflow entry files are named `WORKFLOW.md`, not `SKILL.md`, so
Codex registers only this root router skill instead of exposing every vendored
upstream workflow as a separate skill.

## Workflow Router

Choose the workflow by intent:

| User intent | Read first |
|---|---|
| Deep research, literature review, systematic review, meta-analysis, fact-checking, research question refinement | `ars/deep-research/WORKFLOW.md` |
| Academic paper writing, paper outline, abstract, revision, citation formatting, AI disclosure, LaTeX/DOCX/PDF formatting guidance | `ars/academic-paper/WORKFLOW.md` |
| Paper review, peer review simulation, editorial decision, reviewer calibration, re-review after revision | `ars/academic-paper-reviewer/WORKFLOW.md` |
| End-to-end research-to-paper pipeline, integrity gate, staged review/revision/finalization workflow | `ars/academic-pipeline/WORKFLOW.md` |
| Experiment planning, code experiment execution plan, human study protocol, statistical interpretation, reproducibility validation | `ars/experiment-agent/WORKFLOW.md` |

If the request spans multiple workflows, start with `ars/academic-pipeline/WORKFLOW.md`
unless the user clearly asked for a single phase.

### Paper Topic Scoping Override

Apply this override before the general paper/pipeline routing rule and before the Claude-Style Alias Router below.
The override applies regardless of whether the user invokes ARS via natural
language or via an `ars-*` alias.

If the user says they want to write a paper, thesis, proposal, article, journal
article, or manuscript, but they only provide a broad topic, tentative title,
research interest, or "題目/主題/方向" and do **not** provide a clear,
answerable research question, route to `ars/deep-research/WORKFLOW.md` in
`socratic` mode first. This matches the upstream ARS experience where vague
paper-topic requests start with SCR/Socratic narrowing instead of immediate
outline or drafting.

Treat these as Socratic triggers even when the wording contains paper-writing
intent:

- "I want to write a paper on ..."
- "I have a paper topic/title ..."
- "我想做一篇論文，題目是..."
- "我有一個研究方向/主題，但還不確定問題"
- "幫我想論文題目/收斂研究問題"

First response in this path:

1. State that the request is being routed to `deep-research` `socratic` mode
   because the research question is not yet precise.
2. Ask 3-5 Socratic narrowing questions using `socratic_mentor_agent` and
   `research_question_agent` guidance.
3. Do not produce an outline, draft, literature review, or full pipeline
   dashboard until the user has converged on at least one candidate RQ.

Route directly to `ars/academic-paper/WORKFLOW.md` only when the user already
has a clear RQ, approved study frame, data/results, literature matrix, draft,
or explicitly asks to skip scoping and proceed to outline/drafting. Route to
`ars/academic-pipeline/WORKFLOW.md` only when the user explicitly asks for the
full research-to-paper pipeline or says to continue after Socratic scoping.

## Claude-Style Alias Router

Codex does not install Claude slash commands, but this package emulates their
intent. If the user's request starts with a slash alias (`/ars-plan`) or a plain
alias (`ars-plan`), treat it as a mode shortcut, strip the alias token from the
task text, read the matching `ars/commands/ars-*.md` prompt recipe, then route
to the workflow `WORKFLOW.md` below.

The `model:` field in command frontmatter is a Claude routing hint only. Codex
uses the current model unless the user explicitly requests another model.

| Alias | Read command recipe | Then route to |
|---|---|---|
| `/ars-plan`, `ars-plan` | `ars/commands/ars-plan.md` | `ars/academic-paper/WORKFLOW.md` in `plan` mode |
| `/ars-outline`, `ars-outline` | `ars/commands/ars-outline.md` | `ars/academic-paper/WORKFLOW.md` in `outline-only` mode |
| `/ars-abstract`, `ars-abstract` | `ars/commands/ars-abstract.md` | `ars/academic-paper/WORKFLOW.md` in `abstract-only` mode |
| `/ars-lit-review`, `ars-lit-review` | `ars/commands/ars-lit-review.md` | `ars/academic-paper/WORKFLOW.md` in `lit-review` mode; if the user wants source discovery and synthesis instead, route to `ars/deep-research/WORKFLOW.md` in `lit-review` mode |
| `/ars-citation-check`, `ars-citation-check` | `ars/commands/ars-citation-check.md` | `ars/academic-paper/WORKFLOW.md` in `citation-check` mode |
| `/ars-disclosure`, `ars-disclosure` | `ars/commands/ars-disclosure.md` | `ars/academic-paper/WORKFLOW.md` in `disclosure` mode |
| `/ars-format-convert`, `ars-format-convert` | `ars/commands/ars-format-convert.md` | `ars/academic-paper/WORKFLOW.md` in `format-convert` mode |
| `/ars-revision-coach`, `ars-revision-coach` | `ars/commands/ars-revision-coach.md` | `ars/academic-paper/WORKFLOW.md` in `revision-coach` mode |
| `/ars-revision`, `ars-revision` | `ars/commands/ars-revision.md` | `ars/academic-paper/WORKFLOW.md` in `revision` mode |
| `/ars-full`, `ars-full` | `ars/commands/ars-full.md` | `ars/academic-pipeline/WORKFLOW.md` |

If the request body after the alias is a vague topic, tentative title, research
direction, or "題目/主題/方向" without a clear research question, defer to the Paper Topic Scoping Override above before routing to the alias's target mode.
This applies to `ars-plan`, `ars-outline`, `ars-abstract`, `ars-lit-review`,
and `ars-full`.

If the Codex client reserves slash-prefixed input before it reaches the model,
tell the user to use the plain alias form, for example `ars-plan my topic`.

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
| `ARS_CROSS_MODEL`, `ARS_CROSS_MODEL_SAMPLE_INTERVAL` | Treat upstream secondary-model dispatch instructions as no-op unless the user explicitly asks for cross-model review. When explicitly enabled in this Codex package, use Anthropic Claude Opus 4.7 via API (`ARS_CROSS_MODEL=claude-opus-4.7`, `ANTHROPIC_API_KEY`); do not route this reviewer through Codex/OpenAI APIs. Skip unconfigured cross-model report sections instead of inventing results. |
| `S2_API_KEY`, `OPENALEX_POLITE_EMAIL`, `CROSSREF_POLITE_EMAIL` | These are optional upstream bibliographic lookup settings. Use them only when the user explicitly runs contamination-signal migration or programmatic reference verification; normal Codex routing does not require them. |
| `fresh Claude Code session`, `Claude Code session` | Read as "a new Codex conversation". Material Passport reset semantics still apply; only the runtime changes. This rule covers `ars/academic-pipeline/WORKFLOW.md`, `ars/academic-pipeline/agents/pipeline_orchestrator_agent.md`, `ars/academic-pipeline/references/passport_as_reset_boundary.md`, `ars/experiment-agent/README.md`, `ars/experiment-agent/README.zh-TW.md`, and `ars/docs/PERFORMANCE.md`. |
| `/ars-*` slash command, Claude plugin command | Treat `ars/commands/ars-*.md` as optional prompt recipes. Codex does not register slash commands from this package. |
| SessionStart hook, SubagentStop hook, `hooks/hooks.json` | Treat as upstream Claude Code hook metadata only. Do not install or execute Claude hooks in Codex unless the user explicitly asks to inspect or port a hook. |

## Agent Prompt Use

When a workflow lists agents:

1. Read the workflow `WORKFLOW.md` to identify the mode and phase.
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
`claim_ref_alignment_audit_agent.md`, `collaboration_depth_agent.md`,
`integrity_verification_agent.md`,
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
- `ars/commands/` contains upstream Claude slash-command prompt recipes.
- `ars/hooks/` contains upstream Claude hook metadata preserved for traceability.
- `ars/tests/` contains upstream fixture corpora used by validator tests.

When an ARS file points to `shared/...`, resolve it as `ars/shared/...`.
When it points to another workflow, resolve it under `ars/<workflow>/...`.
When it points to root-level `scripts/...`, `examples/...`, or `docs/...`, resolve
it under `ars/scripts/...`, `ars/examples/...`, or `ars/docs/...`.

## Inactive Upstream Scripts

`manifest.json` lists `inactive_upstream_scripts` that are vendored for
traceability but are not Codex package validation gates. Do not wire them into
Codex CI or treat them as required runtime checks unless the missing upstream
Claude Code inputs, especially `.claude/CLAUDE.md`, are deliberately supplied.

`ars/scripts/run_codex_audit.sh` is vendored because upstream ARS uses it as a
Codex audit wrapper, but follow its own guardrail: it must not be invoked from
the same in-LLM session that produced the audited deliverable.

## Verification Discipline

For claims, citations, references, statistics, journal policies, API behavior, and
current facts, verify against primary or authoritative sources. If verification is
not possible, mark the item as unverified instead of inventing support.

Never fabricate references. For citation existence checks, prefer DOI or official
metadata lookup, then authoritative web search. Semantic Scholar, OpenAlex, and
Crossref API instructions are in `ars/deep-research/references/`; use them only
when the task needs programmatic reference verification.

## Output Defaults

- Default language follows the user's language.
- For Chinese, use Traditional Chinese unless the user requests otherwise.
- For staged workflows, show the current stage, required inputs, output artifact,
  and whether the next gate is optional or mandatory.
- For paper/research outputs, keep uncertainty explicit and separate evidence,
  inference, and recommendation.
