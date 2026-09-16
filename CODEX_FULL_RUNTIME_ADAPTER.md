# Codex Full-Runtime Adapter Guide

This guide documents the optional full-runtime profile for
`academic-research-suite`. Default ARS-Codex execution adapts between inline work and native delegation
through `skills/academic-research-suite/SKILL.md`. This guide covers the separately
opt-in fixed topology and hooks.

## What This Adds

The Codex-only adapter lives under `skills/academic-research-suite/codex/` and
adds four pieces:

1. `full-runtime-manifest.json` defines alias routing, workflow mapping,
   agent-team rules, hook metadata, quality gates, and known degradations.
2. `agents/*.md` defines Codex agent-team templates for deep research,
   academic paper writing, academic pipeline orchestration, paper review, and
   experiment planning.
3. `scripts/ars_codex_full_runtime.py` produces deterministic JSON route plans.
   It is read-only and does not spawn agents or execute hooks.
4. `hooks/` contains a disabled-by-default read-only hook pack. It must be
   manually installed and explicitly enabled before use.

The vendored upstream ARS content remains under
`skills/academic-research-suite/ars/`. The current package manifest pins the
exact upstream commit.

## Enablement

No environment variables are required for normal ARS-Codex use.

Enable full-runtime planning:

```bash
export ARS_CODEX_FULL_RUNTIME=1
```

Enable planner-driven Codex agent-team dispatch:

```bash
export ARS_CODEX_AGENT_TEAM=1
```

Enable the hook pack:

```bash
export ARS_CODEX_HOOKS=1
```

Recommended opt-in profile:

```bash
export ARS_CODEX_FULL_RUNTIME=1
export ARS_CODEX_AGENT_TEAM=1
```

Hooks still require explicit manual installation or a Codex hook configuration
that references `skills/academic-research-suite/codex/hooks/hooks.json`.

## Usage

Default usage:

```text
Use $academic-research-suite. ars-plan Research question: How do quality assurance agencies evaluate AI governance in universities?
```

Planner inspection:

```bash
ARS_CODEX_FULL_RUNTIME=1 ARS_CODEX_AGENT_TEAM=1 \
python3 skills/academic-research-suite/codex/scripts/ars_codex_full_runtime.py --pretty \
  "ars-reviewer full review for this manuscript."
```

## ARS v3.22.0 Runtime Boundaries

The Phase-1 output-language-pair contract is carried through paper intake and
abstract generation into Schema 4. Only `zh-tw-en` is registered; omission
preserves legacy surfaces, and unsupported or malformed values fail visibly.
Spanish activation phrases are routed by the root skill and planner, with
revision and reviewer simulation kept distinct; they do not install a Spanish
output-locale pack. The gate catalog includes hermetic language-pair, file-lock,
and reviewer-calibration tests, while Claude plugin eval suites remain reference
material rather than Codex performance evidence.

- `ARS_CROSS_MODEL_TRANSPORT=codex` is an explicit, contained
  ChatGPT-subscription transport for one-reference citation checks at Stage 2.5
  / 4.5 only. It requires Codex CLI 0.147.0 or newer, `ARS_CROSS_MODEL`, the
  exact `Logged in using ChatGPT` attestation on stdout or stderr, and explicit
  provider/content/cost consent. The provider schema omits unsupported
  `uniqueItems` while the local duplicate-source guard remains fail-closed;
  `code_mode` stays disabled, but the bounded host required by standalone search
  remains available under the closed event grammar. The transport accepts no
  caller-authored prompt or path and never falls back automatically to an API
  or expands to reviewer, DA, calibration, re-review, checkpoint, or handoff calls.
- The citation transport does not accept a result at `turn/completed` alone.
  It closes stdin and requires clean process exit plus stdout/stderr EOF within
  the bounded drain; late forbidden or malformed events, drain timeout,
  nonzero exit, reader failure, and stderr overflow fail visibly.
- Ordinary discovery and inline metadata checks use Codex browsing and
  authoritative metadata. Calling `ars-full` alone does not launch the
  Semantic Scholar, OpenAlex, Crossref, or arXiv Python resolver clients;
  programmatic reference verification must be requested explicitly. The v3.21
  claim-standing path is separate and requires both a user request and
  affirmative plan-bound consent before selected discovery adapters run.
- Local-PDF structural preflight remains the page-anchor authority. The
  `--classify-content` extension is opt-in and process-isolated, uses the
  separately pinned `ars/requirements-pdf-content-classifier.txt`, and emits
  only `TEXT_AVAILABLE` / `OCR_RECOMMENDED` / `unavailable` advisory data with
  `STRUCTURE_ONLY` verdict scope. Missing dependencies stay visibly
  unavailable, and no automatic OCR or anchor gate is enabled.
- Source-bound evidence rows and deterministic review/revision artifacts add
  traceability without replacing integrity verdicts. Revision roadmaps remain
  non-ranking proposals until the author explicitly adjudicates exact choices;
  optional cross-run activity capture is best-effort and nonblocking.
- Review-target context must be author-confirmed, human-subjects authority
  remains institution-owned and unresolved when its two authority axes cannot
  be resolved, and bibliographic/retraction plus preregistration-consistency
  carriers remain advisories. The adapter must not infer author choices,
  venues, institutional approval, legal advice, document agreement, or a clean
  integrity result from these artifacts.
- Research-workflow profiles are a deterministic, default-off substrate. The
  adapter records only an explicit selection or the visible `field_general`
  fallback, performs no manuscript-family inference, and adds no automatic
  planner or pipeline hook; behavioral evidence remains `NOT_RUN`.
- `ARS_INQUIRY_LEDGER=1` enables only the local opt-in alpha. The adapter never
  sets it automatically, and its author events, bounded checkpoint summaries,
  stale-cause accounting, locks, and recovery receipts grant no external call
  authority or outcome claim.
- The sealed promotion-bakeoff schemas and hermetic lifecycle tests are
  vendored. Direct `verify-tree` remains upstream-only because the re-rooted
  snapshot lacks the complete canonical upstream Git history required to prove
  seal/reveal chronology.

## Astra model plan

The [model policy](skills/academic-research-suite/codex/model-runtime-policy.md)
explains the task-based effort choices. Inspect a plan without executing a model:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_full_runtime.py --pretty \
  "ars-reviewer full review for this manuscript."
```

`model_plan.launch_argv` can start a new Codex invocation. `ARS_CODEX_MODEL` and
`ARS_CODEX_REASONING_EFFORT` override the planner policy. Routine work is planned
at `medium`; complex judgement at `xhigh`. These are local policy choices, not
measured ARS optima. `max` and Codex `ultra` remain available explicitly in the
main runtime; citation-only transport rejects `ultra` before launch because it
requests delegation. API Astra effort stops at `max`.

The two `ARS_CODEX_ACTIVE_*` fields only record caller-reported observations;
they neither configure the runtime nor attest that the requested model ran.

## Verification

Run adapter gates from the repository root:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all
```

Run adapter tests:

```bash
python3 -m pytest skills/academic-research-suite/codex/tests -q
python3 -m pytest \
  skills/academic-research-suite/ars/scripts/test_research_workflow_profile.py \
  skills/academic-research-suite/ars/scripts/test_inquiry_branch_ledger.py \
  skills/academic-research-suite/ars/scripts/test_check_data_access_level.py \
  skills/academic-research-suite/ars/scripts/test_review_criteria_binding.py \
  skills/academic-research-suite/ars/scripts/test_check_promotion_bakeoff_preregistration.py
```

## Known Degradations

- Codex does not register Claude Code slash commands. ARS aliases are parsed by
  the root skill and optional planner.
- Native delegation is adaptive and runtime-dependent. Fixed planner topologies
  and hooks remain opt-in; their flags do not gate ordinary collaboration.
- ARS-Codex uses the native Codex plugin marketplace lifecycle; Claude-only
  slash-command registration and hook behavior are not reproduced.
- Hook installation is manual and disabled by default.
- New trusted project sessions use `gpt-6-astra` / `xhigh` from the project
  config. Installed skills cannot switch the current model. The planner emits
  explicit launch arguments and preserves user choices; light-route `sonnet`
  metadata is not a GPT model pin.
- External cross-model verification is never silently simulated.
- The contained Codex citation transport depends on an eligible logged-in
  Codex runtime and explicit consent; it is citation-only and has no automatic
  provider-API fallback.
- Optional PDF content classification needs its separate dependency and remains
  an advisory; absence cannot be promoted to structural `PASS`.
- Deterministic v3.21.1 evidence, review, revision, human-subjects,
  bibliographic, and preregistration artifacts do not substitute for author,
  reviewer, institutional, legal, or domain-expert judgment.
- The vendored tree cannot independently re-prove upstream promotion-bakeoff
  seal/reveal chronology; only the hermetic contract tests are active here.
