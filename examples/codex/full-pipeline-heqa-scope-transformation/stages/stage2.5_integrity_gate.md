# Stage 2.5 — Integrity Gate (MANDATORY)

**Gate type:** 7-mode AI Research Failure Mode Checklist (Lu et al. 2026)
**Runner:** Codex CLI 0.130.0, `codex exec --ephemeral --sandbox read-only`, default model
**Date:** 2026-05-11
**Cost band:** low reasoning effort, ~19k tokens
**Engagement confirmed:** Codex output explicitly states "Stage 2.5 integrity gate engaged"

## Result summary

| Failure mode | Verdict | Reasoning (Codex verbatim) |
|---|---|---|
| 1. Implementation bugs | PASS/N.A. | No implementation, code, or computational pipeline. |
| 2. Hallucinated results | PASS | Outline does not claim empirical findings. |
| 3. Shortcut reliance | PASS | Plausible conceptual progression, though §3 must later define diagnostics rigorously. |
| 4. Bug-as-insight reframing | PASS/N.A. | No failed method being reframed. |
| 5. Methodology fabrication | **HOLD** | Diagnostic dimensions and matrix risk overclaiming analytical precision unless framed as a heuristic typology rather than a validated measurement framework. |
| 6. Frame-lock | **HOLD** | The automation-vs-scope-transformation binary may obscure intermediate or third-category cases (augmentation, governance reconfiguration, institutional capacity building, quality-risk displacement). |
| 7. Citation hallucinations | PASS/N.A. | No citations included yet. |

## Why this is a meaningful regression signal

Stage 2.5 did NOT rubber-stamp the outline. Two HOLD findings (mode 5 + mode 6) demonstrate the integrity gate engages with substantive conceptual critique rather than mechanical PASS-throughs. The frame-lock finding is especially load-bearing for ARS: the gate caught the binary trap before downstream drafting locks it in.

The downstream artifact (`abstract.md`) reflects how these HOLDs were addressed in the original Codex run that produced the published abstract — note the abstract's deliberate use of "scope transformation" as one of several quality-intelligence pathways rather than as a single binary opposed to automation, and its explicit inclusion of "human-centred advisory support" alongside automation and transformation.

## Regression signals to watch

- Integrity gate must explicitly enumerate all 7 modes, not skip any.
- HOLDs must come with one-sentence reasoning (not just a PASS/HOLD tag).
- Gate must not be downgraded to "advisory only" — it is MANDATORY by ARS architecture, and Codex's response treated it as such.
- N.A. classifications for modes 1/4/7 are legitimate for an outline-stage gate (no implementation, no results, no citations yet).
