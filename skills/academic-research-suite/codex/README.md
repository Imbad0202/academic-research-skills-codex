# ARS-Codex Full-Runtime Adapter

This directory is the Codex-only runtime adapter for
`academic-research-suite`. Vendored upstream content remains under `ars/`; do
not hand-edit it except through an explicit upstream sync or documented path
patch.

## Runtime Profiles

Default behavior uses native adaptive execution:

```text
Use $academic-research-suite: ars-plan ...
```

The root router reads the relevant `ars/*/WORKFLOW.md` and agent prompt files,
then works inline or delegates useful independent work through native collaboration.
Read [model/runtime policy](model-runtime-policy.md) for Astra selection and
[the source audit](audits/2026-09-06-model-alignment.md) for the evidence.

The fixed full-runtime topology and hooks are opt-in:

```bash
export ARS_CODEX_FULL_RUNTIME=1
export ARS_CODEX_AGENT_TEAM=1
export ARS_CODEX_HOOKS=1
```

- `ARS_CODEX_FULL_RUNTIME=1` enables structured command routing and gate
  planning through `codex/scripts/ars_codex_full_runtime.py`.
- `ARS_CODEX_AGENT_TEAM=1` permits planner-driven Codex agent-team dispatch
  using templates under `codex/agents/`.
- `ARS_CODEX_HOOKS=1` permits manual installation of the disabled-by-default
  hook pack in `codex/hooks/`.

Without these flags, native adaptive execution remains available. If the runtime
lacks collaboration tools, execute inline and disclose that limitation when
review independence matters. The planner never dispatches agents itself.

Topology experiments require a separate, double opt-in in addition to the
agent-team flags:

```bash
export ARS_CODEX_TOPOLOGY_EXPERIMENT=1
export ARS_CODEX_TOPOLOGY_ARM=reviewer-five-panel
```

Registered arms are `inline-solo`, `reviewer-two-plus-synthesis`,
`reviewer-five-panel`, `reviewer-full-seven`, and `workflow-current`. An arm
variable by itself is ignored. Unknown or workflow-inapplicable arms fail
closed. No experiment changes the native adaptive policy or writes routing state.

## Main Files

- `full-runtime-manifest.json` is the adapter contract: command aliases,
  workflow mapping, agent-team rules, quality gates, hook pack, and known
  degradations.
- `scripts/ars_codex_full_runtime.py` turns a request into a deterministic JSON
  plan. It is read-only and safe to run in tests. Its `quality_gates` inventory
  has scope `package_validation_catalog` and `quality_gates_execute_on_request=false`;
  ordinary research requests use the checks relevant to their workflow.
- `scripts/ars_codex_quality_gates.py` validates adapter packaging, hook safety,
  reviewer independence fixtures, and upstream lock provenance.
- `agents/*.md` are Codex subagent templates. They point back to vendored ARS
  source prompts rather than duplicating upstream prompt bodies.
- `compatibility-matrix.md` records Claude Code parity, remaining gaps, and
  verification methods.
- `topology-experiment/` contains the frozen issue #37 cohort, clean-room
  envelopes, per-run resource receipts, held-out adjudications, and the local
  go/no-go report.

## Agent-Team Semantics

The adapter cannot promise byte-for-byte Claude Code Agent Team behavior.
Instead it provides an explicit Codex orchestration contract:

- reviewer panels produce independent reviewer sections before synthesis;
- synthesis preserves minority and dissenting findings unless resolved by
  evidence and severity;
- pipeline orchestration stops at requested checkpoints;
- new project sessions target `gpt-6-astra` with `xhigh`; the planner recommends
  `medium` for routine work and `xhigh` for complex judgement, preserves explicit
  choices, and distinguishes requested settings from observed execution;
  upstream `sonnet` hints do not select a Codex model;
- ARS v3.22.0 retains model tiering as advisory metadata; it is applied only
  when a Codex runtime provides explicit per-dispatch model selection;
- canonical cross-model handoffs are validated and transported by the
  dispatching context, not by least-privilege owner roles;
- the fixed Reviewer 2 substrate swap and Priority-1 re-review judge pass run
  only after explicit provider configuration and content consent;
- `ARS_CROSS_MODEL_TRANSPORT=codex` explicitly selects the contained
  ChatGPT-subscription transport only for one-reference Stage 2.5 / 4.5
  citation checks; it requires Codex CLI 0.147.0 or newer, `ARS_CROSS_MODEL`,
  the exact `Logged in using ChatGPT` attestation on stdout or stderr, and
  provider/content/cost consent. The provider schema omits unsupported
  `uniqueItems` while local duplicate refusal stays fail-closed; `code_mode`
  remains disabled, but the bounded host needed for standalone search remains
  available under the closed event grammar. It accepts no caller-authored
  prompt or path and has no automatic API fallback or
  reviewer/DA/calibration/re-review/handoff scope;
- the contained citation transport treats `turn/completed` as provisional and
  accepts only after clean process exit plus stdout/stderr EOF; late forbidden
  or malformed events and drain failures remain visible failures;
- citation-cache staleness remains advisory-only, while live re-validation is
  opt-in and surfaced in the route plan;
- local PDFs use the structural read-integrity preflight before page anchors
  are trusted; the v3.20 `--classify-content` extension is opt-in,
  process-isolated, separately pinned, and advisory-only, with
  `STRUCTURE_ONLY` verdict scope and no automatic OCR/anchor gate;
- human-read attestations remain user-owned; every new mark requires an
  explicit `read_scope`, and partial-coverage status remains visible;
- revision rounds retain the claim-strength ladder and deterministic
  token-conservation advisory checks;
- Phase E evidence rows remain source-bound and preserve the existing verdict;
  non-ranking roadmaps require a separate explicit author-adjudication sidecar,
  while optional cross-run adjudication activity is local and advisory only;
- review-target context is author-confirmed and criterion pointers stay aligned
  across formative, internal, and external review without affecting integrity
  verdicts, editorial arithmetic, checkpoints, or author triage. The shipped
  MSR 2027/SIGSOFT proving set demonstrates one exact-profile source-binding
  path, not venue or discipline coverage;
- human-subjects authority keeps review-ethics and data-protection axes
  separate and unresolved states visible; outputs never simulate an IRB/REC,
  legal determination, institutional authorization, or readiness decision;
- bibliographic/retraction and preregistration-consistency carriers preserve
  provenance, staleness, disagreement, and degradation without becoming a
  clean-document certificate, agreement finding, rewrite, or consent record;
- ordinary discovery and inline ingest use Codex browsing; `ars-full` alone
  does not launch the four Python resolver clients, and script-backed citation
  verification remains an explicit programmatic request;
- the v3.21 claim-standing query-plan, affirmative-consent, freshness, and
  transmission sequence is preserved as a separate user-requested advisory
  path; eligibility never dispatches a call;
- the v3.21.1 research-workflow profile substrate is deterministic and
  default-off: only explicit selection or the visible field-general fallback
  is recorded, no manuscript inference or planner/pipeline hook is added, and
  behavioral evidence remains `NOT_RUN`;
- `ARS_INQUIRY_LEDGER=1` enables only the local opt-in branch-ledger alpha;
  the adapter never sets it automatically, and author events, bounded
  summaries, stale causes, path locks, and recovery receipts do not create
  network authority or outcome claims;
- the v3.21.1 data-flow, control-availability, stage-capability, risk, and
  governance transparency surfaces remain available with their deterministic
  validators and without becoming effectiveness or certification claims;
- the v3.21.1 sealed promotion-bakeoff contracts and hermetic tests are
  available, but direct `verify-tree` remains upstream-only because this
  re-rooted snapshot lacks the complete canonical upstream Git history;
- the panel, degradation registry, tools-allowlist, and pipeline-boundary
  validators remain available as vendored quality gates;
- the upstream v3.18 SessionStart update reminder is vendored but not executed
  by the Codex hook pack;
- inline execution remains available when it fits the task or native delegation
  is unavailable; fixed reviewer seats remain a coverage contract.

The canonical topology plan records node dependencies and edge-level
information sharing. Reviewer seats cannot read peer outputs before synthesis;
the seven-node reviewer arm is one field configurer, five blind reviewer seats,
and one synthesizer, not seven reviewers.

## Verification

Run the adapter smoke/parity checks from the repository root:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all
python3 -m pytest skills/academic-research-suite/codex/tests
python3 skills/academic-research-suite/codex/scripts/ars_codex_topology_experiment.py validate --require-runs
```

Run upstream validators from the vendored ARS root as needed:

```bash
cd skills/academic-research-suite/ars
python3 -m pytest scripts/test_codex_router_policy.py
python3 scripts/check_passport_reset_contract.py
python3 scripts/check_v3_9_2_phase_boundary.py
python3 scripts/check_cross_model_handoff_contract.py
python3 scripts/check_degradation_registry.py
python3 scripts/check_pipeline_boundary_semantics.py
python3 scripts/check_tools_allowlist.py
python3 scripts/check_data_flows.py
python3 scripts/check_control_availability.py
python3 scripts/check_stage_capability_matrix.py
python3 scripts/check_risk_register.py
python3 -m pytest scripts/test_verification_cache.py scripts/test_verification_gate.py
python3 -m pytest scripts/test_ars_update_check.py
python3 -m pytest scripts/test_pdf_read_preflight.py scripts/test_ars_mark_read.py
python3 -m pytest scripts/test_check_revision_token_conservation.py
python3 -m pytest scripts/test_cross_model_codex_transport.py
python3 scripts/check_630_codex_subscription_transport.py
python3 scripts/check_evidence_row_integration.py
python3 scripts/check_670_revision_roadmap_integration.py
python3 scripts/check_684_review_criteria_binding.py
python3 scripts/check_human_subjects_output_contract.py
python3 scripts/check_bibliographic_integrity_signals.py
python3 scripts/check_cross_document_consistency_advisory_integration.py
python3 -m pytest scripts/test_research_workflow_profile.py scripts/test_inquiry_branch_ledger.py
python3 -m pytest scripts/test_check_data_access_level.py scripts/test_review_criteria_binding.py
python3 -m pytest scripts/test_check_promotion_bakeoff_preregistration.py
```

Do not run `check_promotion_bakeoff_preregistration.py verify-tree` from this
vendored root; that command requires the complete canonical upstream history.
