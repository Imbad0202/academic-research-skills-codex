---
name: ars-academic-paper-team
runtime: codex-native-adaptive
enabled_when: "Matching ARS workflow; native delegation is optional and fixed planner topology is opt-in"
source_workflow: "ars/academic-paper/WORKFLOW.md"
---

# ARS Academic Paper Team for Codex

Apply [the shared model/runtime policy](../model-runtime-policy.md): Astra is the
Codex target, explicit model choices prevail, and completion requires observable
artifacts. Give each delegated task bounded inputs, outputs and authority.


Use for `academic-paper` modes, inline or with useful native delegation.

## Dispatch Shape

- `plan` mode uses `socratic_mentor_agent.md`, `intake_agent.md`, and
  `structure_architect_agent.md`; it produces a plan and missing-evidence map,
  not a full draft.
- `outline-only` uses `structure_architect_agent.md` and
  `argument_builder_agent.md`.
- `full` mode keeps the generator/evaluator contract from upstream:
  `draft_writer_agent.md` commits its drafting plan before evaluation, and
  `peer_reviewer_agent.md` evaluates the visible draft using evidence-anchored
  categorical criteria. Numeric self-scores are retired.
- `citation-check` uses `citation_compliance_agent.md` and must separate
  missing, mismatched, unverifiable, and format-only citation issues.
- `format-convert` uses `formatter_agent.md`; unresolved high-warning claim
  audit annotations remain blocking when claim audit mode was enabled upstream.

## Output Contract

Preserve Material Passport fields, citation locators, claim-audit annotations,
and venue disclosure requirements. Do not add unsupported claims from model
memory; mark material gaps explicitly.

For abstracts, preserve the `output_language_pair` carrier from intake through
Schema 4, following `ars/shared/output_language_pair.md`. Phase 1 registers only
`zh-tw-en`; an omitted value retains legacy surfaces and stays omitted in the
serialized draft. Unsupported or malformed values fail visibly. The pair does
not choose manuscript-body language or abstract cardinality, and Spanish intent
routing does not supply a Spanish output-locale pack.
