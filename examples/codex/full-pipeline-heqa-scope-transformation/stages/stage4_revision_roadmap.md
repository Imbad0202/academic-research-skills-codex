# Stage 4 — academic-paper (revision-coach mode)

**Workflow routed:** `academic-paper`
**Mode routed:** `revision-coach`
**Runner:** Codex CLI 0.130.0, `codex exec --ephemeral --sandbox read-only`, default model
**Date:** 2026-05-11
**Cost band:** low reasoning effort, ~27.7k tokens

## User prompt (verbatim, reproducible)

```text
Use $academic-research-suite.

Stage 4 REVISION. The Stage 3 review returned Major Revision with 3 concerns:

1. The automation-vs-scope-transformation distinction risks sounding taxonomic rather
   than argumentative — need a sharper conceptual criterion for when HEQA's
   object/temporality/evidence/authority has actually changed.

2. The human-only boundary (values, accountability, peer review, final quality decisions)
   needs stronger normative grounding — democratic legitimacy / professional judgment /
   institutional responsibility / due process / epistemic limits.

3. §4 use cases may sprawl — each example should tie to one specific diagnostic dimension,
   not catalogue AI applications.

Use academic-paper revision-coach mode to produce a REVISION ROADMAP (not a redraft).
Per-concern: priority (P1/P2/P3), action, where it lands in the paper, rough effort.

Codex platform pipeline traversal smoke test:
1. Confirm router routed to academic-paper / revision-coach mode.
2. 3 revision roadmap entries (one per concern).
3. STOP. Do not write revised text.
```

## Revision roadmap (Codex verbatim)

| # | Priority | Concern (from Stage 3) | Action | Where it lands | Effort |
|---|---|---|---|---|---|
| 1 | P1 | Distinction sounds taxonomic, not argumentative | Add a sharper conceptual test: HEQA transformation occurs only when at least one diagnostic dimension changes the **object of judgment, temporal logic, admissible evidence, or authority structure** — not merely when AI accelerates existing procedures. Use this as the paper's argumentative hinge. | §3 conceptual framework; echoed in §1 and §5 | Moderate |
| 2 | P1 | Human-only boundary needs stronger normative grounding | Rebuild the boundary as a normative claim, not a practical limitation: final HEQA judgment remains human because **legitimacy, accountability, professional judgment, institutional responsibility, due process, and epistemic limits cannot be delegated to statistical systems.** | New normative subsection in §3; §5 governance discussion | Moderate–substantial |
| 3 | P2 | §4 use cases may sprawl | Reorganize §4 so each use case is tied to exactly one diagnostic dimension. Remove catalogue-style AI examples; each example shows how to detect transformation along one dimension. | §4; possibly add short diagnostic matrix table | Light–moderate |

## Convergent observation with the imported abstract.md

> Note on provenance: the `../abstract.md` was produced in a separate
> `ars-codex` research session on 2026-05-10 — it is **not** a downstream
> output of the Stage 1–4.5 transcripts captured in this 2026-05-11
> traversal. The observation below is convergent rather than causal: the
> 2026-05-10 abstract independently expresses moves consistent with the
> 2026-05-11 revision roadmap, which is itself evidence of router and
> downstream-agent consistency on the same topic across two sessions.

- **Roadmap #1**: abstract explicitly distinguishes "AI applications that merely automate compliance work" from those that "contribute to quality intelligence, risk-informed governance, continuous monitoring, and human-centred advisory support" — i.e. an argumentative hinge along these lines is present.
- **Roadmap #2**: abstract states "values, accountability, peer review, and final quality decisions must remain human-led" — the normative grounding is present.
- **Roadmap #3**: abstract organizes use cases "across actors such as teachers, departments, institutions, and QA agencies" — an actor-anchored matrix, not an AI-application catalogue.

## Regression signals to watch

- Router must route a "produce revision roadmap, do not redraft" request to `revision-coach`, not `revision` (which would rewrite the text).
- Roadmap must use P1/P2/P3 priority vocabulary (per `parse_review_comments_protocol.md` in the vendored ARS content).
- Action column must be substantive — not "address concern 1" but a concrete writing move.
