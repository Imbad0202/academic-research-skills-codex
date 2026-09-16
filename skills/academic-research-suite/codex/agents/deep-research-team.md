---
name: ars-deep-research-team
runtime: codex-native-adaptive
enabled_when: "Matching ARS workflow; native delegation is optional and fixed planner topology is opt-in"
source_workflow: "ars/deep-research/WORKFLOW.md"
---

# ARS Deep Research Team for Codex

Apply [the shared model/runtime policy](../model-runtime-policy.md): Astra is the
Codex target, explicit model choices prevail, and completion requires observable
artifacts. Give each delegated task bounded inputs, outputs and authority.


Use for `deep-research` modes. Delegate independent searches or evidence checks
when useful and synthesize against their source material.

## Dispatch Shape

- `socratic` mode starts with `socratic_mentor_agent.md` and
  `research_question_agent.md`; it must not produce an outline or draft before
  the research question is precise.
- `lit-review` and `systematic-review` modes start with
  `bibliography_agent.md`, `source_verification_agent.md`, and
  `synthesis_agent.md`.
- `fact-check` mode starts with `source_verification_agent.md` and keeps
  verified / unverified / contradicted claims separate.
- `full` mode may parallelize bibliography, source verification, risk-of-bias,
  ethics, and devil's advocate work after the RQ brief is stable.
- If an explicitly enabled and consented design-freeze owner emits
  `[CROSS-MODEL-HANDOFF v1]`, the team dispatcher validates it with
  `ars/scripts/cross_model_handoff.py`, sends only the payload, and returns a
  divergent result to the original owner for judgment. Malformed handoffs or
  results degrade to `unavailable`.

## Output Contract

Every agent work product must label evidence, inference, and recommendation.
Current facts and citations require verification against authoritative sources
or an explicit unverified marker.
