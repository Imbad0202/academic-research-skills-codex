# Codex-platform pipeline smoke traversal — HEQA Scope Transformation

This directory provides Codex-platform regression evidence under [`CONTRIBUTING.md § Platform ports` L55](https://github.com/Imbad0202/academic-research-skills/blob/main/CONTRIBUTING.md#platform-ports-community-maintained-only)
in the upstream ARS repo: **"at least one full `academic-pipeline` run on
the target platform, committed under an `examples/` path in the sibling
repo, so regressions are detectable."**

## Honest scope

This is a **smoke-level pipeline traversal**, not a production-quality full
run. Trade-offs the reader should know:

- **Each routed stage used the lightest-weight mode** of its workflow:
  Stage 2 = `outline-only` (not `full`), Stage 3 = `quick` (single editor,
  not 5 reviewers + DA), Stage 4 = `revision-coach` (roadmap, not body
  redraft).
- **Stage 3' (re-review) and Stage 4' (second revision loop) are absent.**
  ARS architecture allows up to 2 revision loops; this traversal stops
  after one.
- **Stage 5 (finalize) is imported, not produced in this run.** The
  `abstract.md` + `index.html` come from an earlier `ars-codex` research
  session on 2026-05-10. The Stage 1–4.5 + 6 transcripts in `stages/`
  were generated on 2026-05-11 specifically to provide regression
  evidence for the L55 requirement.
- **Cross-model verification (`ARS_CROSS_MODEL`) was not exercised.**
- **`systematic-review` and `experiment-agent` workflows not exercised.**

What this traversal **does** demonstrate per ARS pipeline architecture:

1. Router classification at every stage transition routed in this run (Stages 1, 2, 3, 4 — verifiable in each stage file). Stage 5 routing is not exercised here because the Stage 5 artifact was imported from a prior session.
2. Both MANDATORY integrity gates (Stage 2.5 + 4.5) engaged with PASS/HOLD
   verdicts per failure mode.
3. Cross-stage handoff: Stage 3 review concerns → Stage 4 roadmap →
   Stage 4.5 regression watchpoints.
4. Stage 6 process summary with the 6-dimension Collaboration Quality
   rubric and the architectural irony caveat.

Regressions in any of these four properties are detectable by re-running
the per-stage prompts in `stages/`.

## Run summary

| Property | Value |
|---|---|
| Target platform | Codex CLI |
| Runner | `codex` 0.130.0 via `codex exec --ephemeral --sandbox read-only` |
| Suite skill | `$academic-research-suite` (single Codex skill, ars-* aliases) |
| Topic | "From Compliance Assurance to Quality Intelligence: A Scope Transformation Matrix for HEQA in the Agentic AI Era" |
| Stage 1–4.5 + 6 transcripts captured | 2026-05-11 |
| Stage 5 artifact (imported) date | 2026-05-10 |
| Approx cost | ~$1–2 OpenAI API (6 `codex exec` calls, low reasoning, ~190k tokens cumulative) |

## Stage map

| Stage | File | Verdict |
|---|---|---|
| 1 — research/socratic | `stages/stage1_research_socratic.md` | Router routed correctly; 3 FINER-aligned narrowing questions |
| 2 — write/outline-only | `stages/stage2_write_outline.md` | 5-section outline; theoretical paper-structure template applied |
| 2.5 — integrity gate | `stages/stage2.5_integrity_gate.md` | 2 HOLD (prompt-numbered modes 5 + 6 = canonical Lu 2026 modes 6 + 7; see file for numbering disclosure) |
| 3 — review/quick | `stages/stage3_review_quick.md` | Major Revision; 3 substantive concerns |
| 4 — revision-coach | `stages/stage4_revision_roadmap.md` | P1/P1/P2 roadmap aligned with the 3 review concerns |
| 4.5 — final integrity | `stages/stage4.5_final_integrity.md` | PASS with 2 drafting watchpoints |
| 5 — finalize | `abstract.md`, `index.html` (imported, 2026-05-10) | Stage 5 artifact from a prior `ars-codex` session, not produced by this 2026-05-11 traversal |
| 6 — process summary | `stages/stage6_process_summary.md` | 6-dim rubric + irony caveat |

## Cross-stage regression signals

The strongest regression signals are at stage transitions:

- **Stage 2.5 → Stage 3**: two independent gates flagged the same
  weakness (frame-lock + overclaim). If a future run shows Stage 2.5
  HOLDs but Stage 3 PASS without addressing them, the reviewer routing
  has regressed.
- **Stage 3 → Stage 4**: revision-coach roadmap items must map 1:1 to
  Stage 3 concerns. Roadmap items #1 / #2 / #3 line up with review
  concerns #1 / #2 / #3.
- **Stage 4 → Stage 4.5**: final integrity must distinguish "cleared by
  revision" from "new watchpoint introduced by revision." This run
  produced two of each — the gate is doing second-order regression
  detection, not just re-running modes.

## What this run does NOT prove

- It does not exercise `ARS_CROSS_MODEL` cross-model verification (would
  require `ANTHROPIC_API_KEY` and is opt-in per ars-codex README).
- It does not exercise `systematic-review` mode (PRISMA) or the
  `experiment-agent` workflow.
- It does not run `academic-paper full` mode (which would invoke the
  v3.6.8 generator-evaluator two-phase contract gate). The vendored
  upstream commit `1d0c8625` is pre-v3.6.8 — see
  `../../../skills/academic-research-suite/manifest.json` for the
  pinned upstream commit.
- The transcripts are **excerpted** from the `codex exec` runs, not
  byte-equivalent reproductions. LLM outputs are not byte-reproducible
  by design (see upstream `shared/artifact_reproducibility_pattern.md`).

## How to re-run for regression check

```bash
# Requires: codex CLI installed and authenticated; $academic-research-suite skill installed.
# Each stage is independent; can re-run any single stage to check that workflow.

cd /path/to/academic-research-skills-codex

# Stage 1 router check (no RQ yet → must route to deep-research socratic)
codex exec --ephemeral --sandbox read-only -c model_reasoning_effort=low \
  "$(cat examples/codex/full-pipeline-heqa-scope-transformation/stages/stage1_research_socratic.md | sed -n '/^## User prompt/,/^## Codex response/p' | sed '1d;$d' | sed 's/^```text$//;s/^```$//')"

# Repeat for stages 2, 2.5, 3, 4, 4.5 — see each stage file for the verbatim user prompt.
```

A regression is detectable if:
- Router classification changes for the same prompt.
- Integrity gates skip modes or stop producing PASS/HOLD verdicts.
- Stage transitions stop carrying forward findings (e.g. Stage 3 PASSes
  when Stage 2.5 had HOLDs and no revision happened in between).
