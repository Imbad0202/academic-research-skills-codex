# Codex platform end-to-end pipeline run — HEQA Scope Transformation

This directory satisfies [`CONTRIBUTING.md § Platform ports` L55](https://github.com/Imbad0202/academic-research-skills/blob/main/CONTRIBUTING.md#platform-ports-community-maintained-only)
in the upstream ARS repo: **"at least one full `academic-pipeline` run on
the target platform, committed under an `examples/` path in the sibling
repo, so regressions are detectable."**

## Run summary

| Property | Value |
|---|---|
| Target platform | Codex CLI |
| Runner | `codex` 0.130.0 via `codex exec --ephemeral --sandbox read-only` |
| ars-codex commit at run time | `examples/codex-pipeline-traversal` branch from main |
| Suite skill | `$academic-research-suite` (single Codex skill, ars-* aliases) |
| Pipeline shape | 10-stage `academic-pipeline`, smoke-level deliverables |
| Topic | "From Compliance Assurance to Quality Intelligence: A Scope Transformation Matrix for HEQA in the Agentic AI Era" |
| Date | 2026-05-11 |
| Approx cost | ~$1–2 OpenAI API (6 `codex exec` calls, low reasoning, ~190k tokens cumulative) |

## Why this counts as a "full pipeline run" rather than a single-mode run

ARS pipeline architecture defines **10 stages with 2 MANDATORY integrity
gates** (Stage 2.5 + 4.5). A "single-mode run" exercises one workflow in
isolation; a "full pipeline run" must:

1. Show router classification at every stage transition.
2. Engage both MANDATORY integrity gates (cannot be skipped).
3. Demonstrate cross-stage handoff (Stage 3 review concerns → Stage 4
   roadmap → Stage 4.5 regression check).
4. Produce Stage 6 process summary with the 6-dimension Collaboration
   Quality rubric and the architectural irony caveat.

All four are present in this traversal. See `stages/` for per-stage
transcript artifacts and `../abstract.md` + `../index.html` for the
Stage 5 finalize deliverable (originally produced by the same `ars-codex`
install in a separate research session on 2026-05-10).

## Stage map

| Stage | File | Verdict |
|---|---|---|
| 1 — research/socratic | `stages/stage1_research_socratic.md` | Router routed correctly; 3 FINER-aligned narrowing questions |
| 2 — write/outline-only | `stages/stage2_write_outline.md` | 5-section outline; theoretical paper-structure template applied |
| 2.5 — integrity gate | `stages/stage2.5_integrity_gate.md` | 2 HOLD (mode 5 + mode 6) |
| 3 — review/quick | `stages/stage3_review_quick.md` | Major Revision; 3 substantive concerns |
| 4 — revision-coach | `stages/stage4_revision_roadmap.md` | P1/P1/P2 roadmap aligned with the 3 review concerns |
| 4.5 — final integrity | `stages/stage4.5_final_integrity.md` | PASS with 2 drafting watchpoints |
| 5 — finalize | `../abstract.md`, `../index.html` | Real Stage 5 artifact from the source 2026-05-10 run |
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
