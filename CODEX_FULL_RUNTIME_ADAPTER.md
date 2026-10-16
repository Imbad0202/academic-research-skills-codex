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
   academic paper writing, academic pipeline orchestration, paper review,
   study screening, and experiment planning.
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

## ARS v3.23.1 Runtime Boundaries

The package tracks the ARS v3.23.1 tag at
`4c5449017f46eb64d112a301d4817d22c7c9f3d9`. Five ARS workflows and the separately
pinned experiment-agent are exposed through one Codex router. Deterministic
tools have synthetic tests; screening accuracy and whether a model follows the
caller instructions remain unmeasured. Upstream Claude audits and
routing/evaluation runs do not measure Codex effectiveness or change the Codex
model policy. Claude startup hooks remain inactive.

- The v3.23.1 CSV importer detects only the delimiter and reads double quotes
  using RFC 4180 rules, including escaped quotes beyond the sniff sample.
- The upstream plugin-prefix and Windows timeout repairs apply to Claude's
  `PreToolUse` write-scope guard. Codex does not install that guard, and its
  optional hook pack only announces metadata. Even upstream, the fence needs
  a named Bucket A agent type; inline roles without that field are not fenced.
- `gemini-4-argon` is the upstream provisional Google verifier recommendation;
  `gemini-3.1-pro-preview` retains its upstream validated status. There is no
  Gemini smoke script or new Codex provider validation. Provider/content/cost
  consent remains required, and native Codex model selection is unchanged.
- The routing core rejects a mid-message `[direct-mode]` escape hatch.
  Upstream #892 remains open after its Claude smoke failed acceptance;
  deterministic Codex tests are not evidence of live model compliance.
- `sr-screener` is an explicitly requested workflow with eight modes:
  `protocol`, `quick`, `pilot`, `ta-screen`, `ft-screen`, `adjudicate`, `audit`,
  and `report`. A request for `deep-research` `systematic-review` does not
  activate screening or cause an automatic handoff. The author confirms the
  eligibility rules; two blinded reviewer roles and an adjudicator provide
  decision support for the review team to verify. Missing or malformed
  decisions stay pending.
- Full title/abstract screening requires a pilot compared with the team's
  labels that misses no record the team advanced, unless the author records
  an override. A reproducible sample of joint exclusions (minimum 20, default
  100; all when fewer are available) requires senior-reviewer QC before counts
  become final. Spreadsheet
  exports neutralise formula text. Upstream Sonnet screening defaults are
  Claude metadata; native Codex execution follows the active model policy.
- The external v3.6.7 Audit Artifact Gate is disabled by default and requires
  `ARS_AUDIT_ARTIFACT_GATE=1` plus explicit run-bound consent to invoke the
  external wrapper. Stage 2.5 and 4.5 integrity gates remain in force.
  Experiment intake is recorded from the scholar's answer before the first
  writer or integrity gate that needs it, never inferred from the manuscript.
- Run-wide constraints enter `standing_constraints[]` only after author
  confirmation and retain the author's words. Applicable dispatches quote
  them; review stages apply them at the author checkpoint to preserve review
  blindness. A declined-only Major keeps the review decision and can offer an
  author-approved limitations-only revision. Finalization creates only the
  requested files, with opt-in Stage 5 refusals surfaced at Stage 4.5.
- Integrity checkpoints replay the evidence rows from the folder named by the
  orchestrator, apply a consistent policy, and retain paywalled sources as
  notes. A source found fabricated stays excluded from later revisions.
- Per-source method weaknesses distinguish author-acknowledged limitations
  from reader inferences and preserve read-scope limits. The fixed-point
  review-form note leaves the choice with the author; it never selects or
  ranks a review form or starts screening.
- `ars-citation-check` now omits the upstream model pin alongside `ars-full`,
  `ars-reviewer`, and `ars-revision-coach`. These four commands inherit the
  session model; remaining `sonnet` hints do not select a Codex model.

- With a passport file, pipeline prompts instruct the caller to use
  `ars/scripts/run_ledger.py` to record exact user words, checkpoint exchanges,
  step receipts, counters, and file hashes locally beside the passport. The
  ledger contains the user's original wording; its storage and deletion are
  documented in `ars/docs/DATA_FLOWS.md`. After compaction, resume, and subagent
  returns, `report --render en` or `--render zh-TW` supplies the handoff check
  verbatim when it has findings. Append computes named input hashes and report
  rechecks them; missing or changed inputs cannot back a completed step.
  The caller reads entries only through `report` or `show`, which share the
  trusted-reader break rule; parse errors give the error kind and position
  without quoting ledger text. A missing or unreadable ledger backs nothing,
  and a broken hash chain backs nothing from the break onward. The chain
  detects accidental damage, not
  deliberate edits, a lost tail, or rollback. Skill deliverable ownership and
  ledger entries do not independently establish or widen user authorization.
- The dispatching session runs `ars/scripts/check_acronyms.py` locally on saved
  drafts and abstracts at the workflow's specified points. This read-only check
  makes no model call and reports partial or unavailable coverage explicitly.
  A review attachment is added after the decision is final and stays outside
  decision, roadmap, and re-review criteria; revision fixes stay within the
  author's authorized targets.
- The instruction/data boundary covers third-party text in workflow intake,
  dispatches, passport imports, and receiver tool reads. The opt-in claim-audit
  prompt version changes with its boundary, preventing old prompt verdicts
  from being reused. These prompt rules are not measured security guarantees.
- Explicit requests retain their selected mode when required inputs are
  missing; literature-review intake does not reopen workflow selection, and
  journal/conference peer review does not trigger the committee-correspondence
  variant. Chinese APA 7 citation checks preserve abbreviation exceptions and
  complete reference authors, require evidence for a stroke-order correction,
  and distinguish visible syntax errors from unverified source claims.

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
