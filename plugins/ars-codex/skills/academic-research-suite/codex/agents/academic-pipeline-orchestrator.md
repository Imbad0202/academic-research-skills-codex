---
name: ars-academic-pipeline-orchestrator
runtime: codex-agent-team
enabled_when: "ARS_CODEX_FULL_RUNTIME=1 and ARS_CODEX_AGENT_TEAM=1"
source_workflow: "ars/academic-pipeline/WORKFLOW.md"
---

# ARS Academic Pipeline Orchestrator for Codex

Use this template for `ars-full` and natural full-pipeline requests when
full-runtime agent-team mode is explicitly enabled.

## Dispatch Shape

The orchestrator owns stage boundaries and checkpoint stops. It may dispatch
workflow teams, but it must not silently run past a requested checkpoint.

Required starting roles:

1. `ars/academic-pipeline/agents/pipeline_orchestrator_agent.md`
2. `ars/academic-pipeline/agents/state_tracker_agent.md`
3. `ars/academic-pipeline/agents/integrity_verification_agent.md`

Optional gate roles:

- `claim_ref_alignment_audit_agent.md` when `ARS_CLAIM_AUDIT=1`.
- `collaboration_depth_agent.md` at advisory checkpoints only.

## Checkpoint Contract

- Every completed stage ends with a visible checkpoint.
- Stage 2.5 and Stage 4.5 integrity gates are mandatory and cannot be diluted
  by advisory observer work.
- Stage 2.5 claim verification covers every HIGH-IMPACT claim plus the random
  sentinel and top-up floor defined by the v3.18 sampling contract. Scope-
  conformance and search-bounded novelty rows remain advisory-only.
- Citation-cache age rows remain advisory-only. Run live bibliographic
  re-validation only when `ARS_CACHE_REVALIDATE=1` was explicitly requested.
- The Stage 5 entry gate is the mandatory finalization boundary. Stage 5's
  completion checkpoint is FULL, and Stage 6 ends only after its decline path
  or terminal acknowledgement is recorded by the state tracker.
- `ARS_PASSPORT_RESET=1` promotes eligible checkpoints to Material Passport
  reset boundaries. The reset ledger must remain append-only.
- If the user asks to stop after intake, dashboard, RQ brief, or another named
  checkpoint, stop there and report the next gate instead of continuing.

## Cross-Model Dispatcher Contract

When cross-model verification was explicitly requested and consented, recognize
`[CROSS-MODEL-HANDOFF v1]` from a dispatched owner as a transport request, not
as a deliverable. Validate it with `ars/scripts/cross_model_handoff.py`, send
only the payload to the configured provider, apply the closed agreement or
divergence routing, and return any judgment work to the original owner.
Malformed handoffs or results become `unavailable`; never repair or invent them.

For Stage 3 `full` review, the consented cross-model reviewer track swaps the
existing Reviewer 2 seat and records panel provenance. At Stage 3' re-review,
run the independent Priority-1 judge pass when configured and carry its Judge
Record forward; divergence triggers synthesis review and never acts as a vote.

## Output Contract

Emit current stage, requested checkpoint, active gate, Material Passport status,
and degraded runtime behavior, if any.
