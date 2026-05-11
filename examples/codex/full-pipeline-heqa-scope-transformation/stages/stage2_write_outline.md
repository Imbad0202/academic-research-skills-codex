# Stage 2 — academic-paper (outline-only mode)

**Workflow routed:** `academic-paper`
**Mode routed:** `outline-only`
**Router agent inferred from transcript:** `structure_architect_agent` (named in the routing scaffold text that preceded the outline in this run; verbatim transcript not committed — verifiable by re-running the verbatim user prompt below)
**Runner:** Codex CLI 0.130.0, `codex exec --ephemeral --sandbox read-only`, default model
**Date:** 2026-05-11
**Cost band:** low reasoning effort, ~27.5k tokens

## User prompt

```text
Use $academic-research-suite.

The Socratic scoping converged on the following research question:

RQ: How does agentic AI reshape the scope of higher education quality
assurance (HEQA) — and what analytical framework can distinguish
AI-as-automation use cases from AI-as-scope-transformation use cases?

Now please move to Stage 2 (WRITE). Use the academic-paper outline-only
mode to produce a 5-section outline for a conceptual framework paper on
this RQ. Target venue: HEQA / educational research conceptual journal.
Length: section titles + 2-3 bullet points per section. APA 7, English.

Codex platform pipeline traversal smoke test:
1. Confirm router routed this to academic-paper / outline-only.
2. Produce the 5-section outline.
3. STOP after outline. Do not draft body.
```

## Codex response (5-section outline)

**§1. Introduction: Agentic AI as a Boundary Problem for HEQA**
- Frame the RQ: agentic AI may alter what counts as assessable educational quality, institutional responsibility, evidence, and continuous improvement.
- Position the paper within HEQA as a conceptual framework paper, not empirical evaluation.
- Establish the core distinction: AI-as-automation preserves the QA object; AI-as-scope-transformation changes the object, actors, evidence base, or temporal horizon.

**§2. Conceptual Background: From QA Processes to QA Scope**
- Review HEQA: standards, accountability, enhancement, evidence, stakeholder trust, institutional learning.
- Define agentic AI: goal-directed planning, tool use, delegated action, adaptive monitoring, semi-autonomous decision support.
- Argue that conventional "efficiency" framings overlook changes in agency, judgment, auditability, and the unit of QA.

**§3. Analytical Framework: Automation Versus Scope Transformation**
- Two-category heuristic: automation improves existing QA routines; scope-transformation reconfigures the QA problem.
- Diagnostic dimensions: task ontology, decision authority, evidence generation, accountability locus, temporal rhythm, stakeholder participation, institutional learning.
- Framework matrix: low-scope automation, high-stakes automation, bounded scope extension, full scope transformation.

**§4. Applying the Framework to HEQA Use Cases**
- Automation cases: document checking, evidence collation, rubric alignment, accreditation drafting, compliance monitoring, risk flagging.
- Scope-transformation cases: continuous curriculum sensing, agent-mediated student experience monitoring, adaptive program review, synthetic evidence infrastructures, AI-enabled institutional self-study.
- Show that the same system can change category depending on governance, oversight, and whether it changes QA questions rather than answering them faster.

**§5. Implications for HEQA Research, Governance, and Future Inquiry**
- HEQA frameworks should evaluate epistemic validity, accountability chains, institutional capacity, legitimacy of AI-mediated judgments — not only AI performance.
- Research directions: comparative case studies, framework validation, trust studies, auditability standards, typologies of AI-mediated evidence.
- Treat agentic AI as scope-shaping infrastructure for HEQA.

## Regression signals to watch

- Router classifies "5-section outline only" to `academic-paper outline-only`, NOT `full`.
- Outline structure aligned with `theoretical` paper-structure template (per the structure_architect routing table visible in transcript, theoretical: Framework/Method 30%, Analysis 25%, Conclusion 8%).
- Stage 2 stops before any body drafting — no abstract, no full prose paragraphs.
