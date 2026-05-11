# Stage 2.5 — Integrity Gate (MANDATORY)

**Gate type:** 7-mode AI Research Failure Mode Checklist (Lu et al. 2026)
**Runner:** Codex CLI 0.130.0, `codex exec --ephemeral --sandbox read-only`, default model
**Date:** 2026-05-11
**Cost band:** low reasoning effort, ~19k tokens
**Engagement confirmed:** Codex output explicitly states "Stage 2.5 integrity gate engaged"

## User prompt (verbatim, reproducible)

```text
Use $academic-research-suite.

We just produced a 5-section outline (Stage 2) for a conceptual framework paper:

RQ: How does agentic AI reshape the scope of higher education quality assurance (HEQA),
and what analytical framework can distinguish AI-as-automation from
AI-as-scope-transformation use cases?

Outline:
§1 Introduction (boundary problem); §2 Conceptual background (HEQA + agentic AI);
§3 Analytical framework (automation vs scope transformation, with diagnostic
dimensions and a 2x2-ish matrix); §4 Applying to HEQA use cases (automation cases +
scope-transformation cases); §5 Implications + future research.

Now run Stage 2.5 INTEGRITY GATE for the OUTLINE only — apply the 7-mode AI Research
Failure Mode Checklist:
1) implementation bugs (N/A for conceptual paper),
2) hallucinated results,
3) shortcut reliance,
4) bug-as-insight reframing,
5) methodology fabrication,
6) frame-lock,
7) citation hallucinations (N/A for outline since no citations yet).

For a conceptual outline, focus on mode 5 (methodology fabrication: any framework
dimensions that overclaim?) and mode 6 (frame-lock: did the outline get stuck in
automation-vs-transformation binary that hides a third category?).

Codex platform pipeline traversal smoke test:
1. Confirm Stage 2.5 integrity gate engaged.
2. Report PASS/HOLD per mode with one sentence reasoning.
3. STOP.
```

## Numbering disclosure

The Stage 2.5 user prompt (see below) enumerated the 7 modes in a non-canonical order (mode 5 = methodology fabrication, mode 6 = frame-lock, mode 7 = citation hallucinations). The Codex response below follows the user-prompt numbering verbatim. **Canonical numbering per Lu et al. (2026) and ARS `academic-pipeline/references/ai_research_failure_modes.md` is:** 1 = implementation bug, 2 = hallucinated citation, 3 = hallucinated experimental result, 4 = shortcut reliance, 5 = implementation-bug-as-insight, 6 = methodology fabrication, 7 = frame-lock. Stage 4.5 in this same traversal uses the canonical numbering; the conceptual findings are identical, only the integer labels differ. Future runs should use canonical numbering in the prompt.

## Result summary (Codex verbatim — non-canonical numbering)

| Mode # (per user prompt) | Canonical mode | Verdict | Reasoning (Codex verbatim) |
|---|---|---|---|
| 1. Implementation bugs | Canonical Mode 1 | PASS/N.A. | No implementation, code, or computational pipeline. |
| 2. Hallucinated results | Canonical Mode 3 | PASS | Outline does not claim empirical findings. |
| 3. Shortcut reliance | Canonical Mode 4 | PASS | Plausible conceptual progression, though §3 must later define diagnostics rigorously. |
| 4. Bug-as-insight reframing | Canonical Mode 5 | PASS/N.A. | No failed method being reframed. |
| 5. Methodology fabrication | Canonical Mode 6 | **HOLD** | Diagnostic dimensions and matrix risk overclaiming analytical precision unless framed as a heuristic typology rather than a validated measurement framework. |
| 6. Frame-lock | Canonical Mode 7 | **HOLD** | The automation-vs-scope-transformation binary may obscure intermediate or third-category cases (augmentation, governance reconfiguration, institutional capacity building, quality-risk displacement). |
| 7. Citation hallucinations | Canonical Mode 2 | PASS/N.A. | No citations included yet. |

## Why this is a meaningful regression signal

Stage 2.5 did NOT rubber-stamp the outline. Two HOLD findings (canonical modes 6 + 7 — methodology fabrication + frame-lock; reported as prompt-numbered modes 5 + 6 in the Codex output above) demonstrate the integrity gate engages with substantive conceptual critique rather than mechanical PASS-throughs. The frame-lock finding is especially load-bearing for ARS: the gate caught the binary trap before downstream drafting locks it in.

The downstream artifact (`abstract.md`) reflects how these HOLDs were addressed in the original Codex run that produced the published abstract — note the abstract's deliberate use of "scope transformation" as one of several quality-intelligence pathways rather than as a single binary opposed to automation, and its explicit inclusion of "human-centred advisory support" alongside automation and transformation.

## Regression signals to watch

- Integrity gate must explicitly enumerate all 7 modes, not skip any.
- HOLDs must come with one-sentence reasoning (not just a PASS/HOLD tag).
- Gate must not be downgraded to "advisory only" — it is MANDATORY by ARS architecture, and Codex's response treated it as such.
- N.A. classifications for prompt-numbered modes 1/4/7 (canonical 1/5/2) are legitimate for an outline-stage gate (no implementation, no implementation-as-insight, no citations yet).
- Future runs should phrase the user prompt in canonical Lu 2026 numbering so the verbatim Codex output matches ARS docs without translation.
