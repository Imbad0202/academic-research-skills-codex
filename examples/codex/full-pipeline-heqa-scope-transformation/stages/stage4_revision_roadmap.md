# Stage 4 — academic-paper (revision-coach mode)

**Workflow routed:** `academic-paper`
**Mode routed:** `revision-coach`
**Runner:** Codex CLI 0.130.0, `codex exec --ephemeral --sandbox read-only`, default model
**Date:** 2026-05-11
**Cost band:** low reasoning effort, ~27.7k tokens

## Revision roadmap (Codex verbatim)

| # | Priority | Concern (from Stage 3) | Action | Where it lands | Effort |
|---|---|---|---|---|---|
| 1 | P1 | Distinction sounds taxonomic, not argumentative | Add a sharper conceptual test: HEQA transformation occurs only when at least one diagnostic dimension changes the **object of judgment, temporal logic, admissible evidence, or authority structure** — not merely when AI accelerates existing procedures. Use this as the paper's argumentative hinge. | §3 conceptual framework; echoed in §1 and §5 | Moderate |
| 2 | P1 | Human-only boundary needs stronger normative grounding | Rebuild the boundary as a normative claim, not a practical limitation: final HEQA judgment remains human because **legitimacy, accountability, professional judgment, institutional responsibility, due process, and epistemic limits cannot be delegated to statistical systems.** | New normative subsection in §3; §5 governance discussion | Moderate–substantial |
| 3 | P2 | §4 use cases may sprawl | Reorganize §4 so each use case is tied to exactly one diagnostic dimension. Remove catalogue-style AI examples; each example shows how to detect transformation along one dimension. | §4; possibly add short diagnostic matrix table | Light–moderate |

## How this aligns with the actual abstract.md

The abstract (the eventual Stage 5 finalize artifact, see `../abstract.md`) reflects all three roadmap moves:

- **Roadmap #1**: abstract explicitly distinguishes "AI applications that merely automate compliance work" from those that "contribute to quality intelligence, risk-informed governance, continuous monitoring, and human-centred advisory support" — i.e. the argumentative hinge landed.
- **Roadmap #2**: abstract states "values, accountability, peer review, and final quality decisions must remain human-led" — the normative grounding made it into the abstract framing.
- **Roadmap #3**: abstract organizes use cases "across actors such as teachers, departments, institutions, and QA agencies" — i.e. an actor-anchored matrix rather than an AI-application catalogue.

## Regression signals to watch

- Router must route a "produce revision roadmap, do not redraft" request to `revision-coach`, not `revision` (which would rewrite the text).
- Roadmap must use P1/P2/P3 priority vocabulary (per `parse_review_comments_protocol.md` in the vendored ARS content).
- Action column must be substantive — not "address concern 1" but a concrete writing move.
