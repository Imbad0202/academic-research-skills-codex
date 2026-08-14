# Codex Full-Runtime Adapter Guide

This guide documents the optional full-runtime profile for
`academic-research-suite`. The default ARS-Codex behavior remains inline
role-prompt execution through `skills/academic-research-suite/SKILL.md`.

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

Default inline usage:

```text
Use $academic-research-suite. ars-plan Research question: How do quality assurance agencies evaluate AI governance in universities?
```

Planner inspection:

```bash
ARS_CODEX_FULL_RUNTIME=1 ARS_CODEX_AGENT_TEAM=1 \
python3 skills/academic-research-suite/codex/scripts/ars_codex_full_runtime.py --pretty \
  "ars-reviewer full review for this manuscript."
```

## ARS v3.20 Runtime Boundaries

- `ARS_CROSS_MODEL_TRANSPORT=codex` is an explicit, contained
  ChatGPT-subscription transport for one-reference citation checks at Stage 2.5
  / 4.5 only. It requires Codex CLI 0.147.0 or newer, `ARS_CROSS_MODEL`, the
  exact `Logged in using ChatGPT` attestation, and explicit
  provider/content/cost consent, accepts no caller-authored prompt or path, and
  never falls back automatically to an API or expands to reviewer, DA,
  calibration, re-review, checkpoint, or handoff calls.
- The citation transport does not accept a result at `turn/completed` alone.
  It closes stdin and requires clean process exit plus stdout/stderr EOF within
  the bounded drain; late forbidden or malformed events, drain timeout,
  nonzero exit, reader failure, and stderr overflow fail visibly.
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

## Verification

Run adapter gates from the repository root:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all
```

Run adapter tests:

```bash
python3 -m pytest skills/academic-research-suite/codex/tests -q
```

## Known Degradations

- Codex does not register Claude Code slash commands. ARS aliases are parsed by
  the root skill and optional planner.
- Codex agent-team behavior is opt-in and runtime-dependent. Inline execution
  remains the default.
- ARS-Codex uses the native Codex plugin marketplace lifecycle; Claude-only
  slash-command registration and hook behavior are not reproduced.
- Hook installation is manual and disabled by default.
- The heavy `ars-full`, `ars-reviewer`, and `ars-revision-coach` routes have no
  v3.20 model frontmatter and inherit the active Codex session model. Light
  routes retain upstream `sonnet` metadata, but the adapter does not force a
  Codex model unless the user or runtime explicitly overrides it.
- External cross-model verification is never silently simulated.
- The contained Codex citation transport depends on an eligible logged-in
  Codex runtime and explicit consent; it is citation-only and has no automatic
  provider-API fallback.
- Optional PDF content classification needs its separate dependency and remains
  an advisory; absence cannot be promoted to structural `PASS`.
- Deterministic v3.20 evidence, review, revision, human-subjects,
  bibliographic, and preregistration artifacts do not substitute for author,
  reviewer, institutional, legal, or domain-expert judgment.
