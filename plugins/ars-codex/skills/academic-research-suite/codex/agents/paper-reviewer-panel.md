---
name: ars-paper-reviewer-panel
runtime: codex-native-adaptive
enabled_when: "Matching ARS workflow; native delegation is optional and fixed planner topology is opt-in"
source_workflow: "ars/academic-paper-reviewer/WORKFLOW.md"
---

# ARS Paper Reviewer Panel for Codex

Apply [the shared model/runtime policy](../model-runtime-policy.md): Astra is the
Codex target, explicit model choices prevail, and completion requires observable
artifacts. Give each delegated task bounded inputs, outputs and authority.


Use this template for native reviewer delegation or inline role execution.
Keep the required review coverage and disclose which execution actually occurred.

## Source Prompts

Read `ars/academic-paper-reviewer/WORKFLOW.md`, then dispatch or emulate these
roles:

1. `ars/academic-paper-reviewer/agents/field_analyst_agent.md`
2. `ars/academic-paper-reviewer/agents/eic_agent.md`
3. `ars/academic-paper-reviewer/agents/methodology_reviewer_agent.md`
4. `ars/academic-paper-reviewer/agents/domain_reviewer_agent.md`
5. `ars/academic-paper-reviewer/agents/perspective_reviewer_agent.md`
6. `ars/academic-paper-reviewer/agents/devils_advocate_reviewer_agent.md`
7. `ars/academic-paper-reviewer/agents/editorial_synthesizer_agent.md`

## Independence Contract

- Produce the journal-fit, methodology, domain, interdisciplinary, and devil's advocate
  reviewer sections before the editorial synthesis.
- Do not expose one independent reviewer's draft output to another reviewer
  before both have completed their own section.
- The editorial synthesizer may see all completed reviewer sections.
- The synthesis must preserve minority and dissenting findings unless it
  explicitly resolves them by severity and evidence.
- Devil's advocate concerns cannot be erased by majority vote. Record whether
  each concern is retained, downgraded, or rejected, and why.
- Run `ars/scripts/check_panel_synthesis.py` on the structured reviewer and
  synthesis artifacts when the full panel contract is active.

## Cross-Model Dispatcher Contract

If an explicitly enabled and consented reviewer owner emits
`[CROSS-MODEL-HANDOFF v1]`, the panel dispatcher validates the envelope and
transports only its payload. Agreement is filled mechanically; divergence or a
full-return DA result goes back to the original owner. A malformed envelope or
result degrades to `unavailable` and is never treated as an ordinary review.

In `full` mode only, when the provider is configured and the user has consented
to sending the manuscript, run `domain_reviewer_agent` as Reviewer 2 on the
cross-model family. This is a substrate swap inside the fixed five-seat panel,
not an added sixth reviewer. Preserve the two-call sprint-contract boundary,
compute no cross-family aggregate, and fill the Decision Letter's Review Panel
Provenance block. If dispatch fails or the track is not active, use the primary
family and disclose the fallback or single-family caveat.

In `re-review`, apply the independent cross-model verdict pass to each Priority
1 roadmap item only after the primary verdicts are committed. A divergence is
a synthesis review trigger, never a vote or automatic overwrite. Emit the
Judge Record and never omit the single-family disclosure when the pass is not
configured or wholly unavailable.

## Output Contract

The full-mode output must contain these top-level sections in order:

1. `Independent Reviewer: Journal-Fit`
2. `Independent Reviewer: Methodology`
3. `Independent Reviewer: Domain`
4. `Independent Reviewer: Interdisciplinary`
5. `Independent Reviewer: Devil's Advocate`
6. `Editorial Synthesis`
7. `Decision Letter`
8. `Revision Roadmap`

The Decision Letter must include the v3.18 Review Panel Provenance block in
`full` mode.

If Codex subagents are unavailable, declare `agent_team_degraded: inline` and
preserve the same section ordering.
