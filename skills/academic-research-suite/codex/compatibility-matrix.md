# ARS-Codex Compatibility Matrix

Audit date: 2026-08-14

## Provenance

| Surface | Evidence |
|---|---|
| Codex package repo | `academic-research-skills-codex` current working tree before release commit |
| Upstream Claude Code repo | Tracked in `skills/academic-research-suite/manifest.json` |
| Upstream suite version | `v3.20.0` |
| Upstream component versions | deep-research `2.12.0`; academic-paper `3.3.0`; academic-paper-reviewer `1.11.0`; academic-pipeline `3.20.0` |
| Codex package version | `0.1.25` |
| License | CC BY-NC 4.0 in upstream and Codex package |
| Upstream sync status | Vendored `ars/` content synced to ARS release `v3.20.0` (peeled commit `3af9f03d5aadb0bca51af1440f20b5cbf97d6dba`); Codex adapter profile retained |
| Codex-only adapter location | `skills/academic-research-suite/codex/` |

## Matrix

| Capability | Default Codex Status | Optional Full-Runtime Profile | Parity Level | Implementation Location | Verification Method | Remaining Risk |
|---|---|---|---|---|---|---|
| Install / update | Native `ars-codex` plugin from the repo marketplace, with direct skill install retained as an alternative | No change to runtime profile | near | `.agents/plugins/marketplace.json`, `plugins/ars-codex/`, `README.md` | plugin validator; `desktop-plugin-bundle` gate; `/skills` | Marketplace users must refresh the Git snapshot before reinstalling an update |
| `ars-*` aliases | Root router emulates Claude command intent | Deterministic planner emits the same alias route metadata | near | `SKILL.md`, `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; manifest gate | Slash-prefixed input can still be intercepted by a client |
| Vague paper-topic routing | Root router sends vague paper topics to Socratic scoping | Planner preserves the same override | near | `SKILL.md`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; upstream router tests | Natural-language routing is still heuristic outside smoke cases |
| Agent prompts | `agents/*.md` are read inline as role/phase prompts | `codex/agents/*.md` provides opt-in agent-team templates pointing back to source prompts | near | `ars/*/agents/*.md`, `codex/agents/*.md` | manifest gate; reviewer fixture gate | Actual subagent availability depends on the active Codex runtime |
| Agent least privilege | Protected top-level agent `tools:` allowlists remain role boundaries; inline use does not widen authority | Dispatched protected roles receive no Bash or network transport; the dispatcher owns cross-model transport | near | `ars/agents/*.md`, `ars/scripts/check_tools_allowlist.py`, `SKILL.md` | upstream tools-allowlist lint and tests | Actual enforcement still depends on the active Codex runtime's tool controls |
| Reviewer independence | Inline mode must preserve independent reviewer sections before synthesis | Agent-team planner orders independent reviewer sections before editorial synthesis | near | `codex/agents/paper-reviewer-panel.md`, `codex/tests/fixtures/reviewer_full_independent_sections.md` | reviewer fixture gate; adapter pytest | Inline runs rely on faithfully preserving section boundaries |
| Executable panel synthesis | Reviewer artifacts can be checked with the vendored closed-grammar panel checker | Planner exposes the checker as a review quality gate | near | `ars/scripts/check_panel_synthesis.py`, `codex/full-runtime-manifest.json` | upstream panel checker tests | The checker validates artifact self-consistency, not substantive correctness |
| Hooks and update reminder | Upstream Claude hooks and the v3.18 SessionStart update checker are metadata only | Disabled-by-default read-only Codex hook pack; no automatic upstream update check | partial | `ars/scripts/ars_update_check.sh`, `codex/hooks/hooks.json`, `codex/scripts/ars_codex_hook.py` | `hook-safety` gate; upstream update-check tests | Plugin users refresh and re-add the marketplace package; direct skill users reinstall or pull |
| Model routing | Heavy `ars-full`, `ars-reviewer`, and `ars-revision-coach` routes have no v3.20 model frontmatter and inherit the session model; light routes retain `sonnet` metadata | Planner reports `inherit` or the light-route hint without forcing model changes | partial | `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; plan inspection | Not equivalent to Claude Code model pinning |
| ARS model tiering | Unset preserves the active Codex model | Planner surfaces `economy` / `quality-boost` as advisory metadata; classification is applied only when per-dispatch model selection exists | partial | `ars/shared/model_tiering.md`, `ars/scripts/model_tiering_manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | upstream tiering lint; adapter pytest | Codex runtimes may not expose relative-tier or per-dispatch model control |
| Material Passport | Prompt/procedure plus vendored validators | Full-runtime manifest exposes passport reset as a quality gate | near | `ars/scripts/check_passport_reset_contract.py`, `codex/full-runtime-manifest.json` | upstream validator; adapter gate | Runtime context isolation is procedural, not a hard sandbox |
| Citation cache staleness and re-validation | Cached verification remains the default; stale rows are advisory-only | Planner surfaces the threshold and whether live re-validation was requested | near | `ars/scripts/verification_cache.py`, `ars/scripts/verification_gate/`, `codex/scripts/ars_codex_full_runtime.py` | upstream cache/gate tests; adapter pytest | Live re-validation depends on external bibliographic services |
| Local-PDF read integrity | Locally read PDFs receive the structural preflight before page anchors are trusted; `--classify-content` optionally adds a process-isolated text/OCR advisory | Planner contract requires Stage 1 sidecars, freshness checks, and distinct FAIL/UNAVAILABLE handling; classification never changes the `STRUCTURE_ONLY` verdict scope | near | `ars/scripts/pdf_read_preflight.py`, `ars/scripts/pdf_content_classifier_worker.py`, `ars/requirements-pdf-content-classifier.txt` | upstream preflight/classifier tests; boundary validator | Missing optional dependencies produce deterministic `UNAVAILABLE`; classifier output is not an automatic OCR or anchor gate |
| Human-read scope | Optional `read_scope` is written only from user declarations; partial coverage remains visible | Orchestrator contract carries ledger scope into finalizer decisions | near | `ars/scripts/ars_mark_read.py`, `ars/shared/contracts/passport/human_read_log.schema.json` | upstream mark-read and finalizer tests | Legacy marks without scope intentionally resolve as unknown |
| Revision claim-drift guards | Claim-strength changes and conserved tokens are checked advisory-first for every revision round | Planner contract carries the Revision-Evidence Bundle across rounds | near | `ars/shared/references/claim_strength_ladder.md`, `ars/scripts/check_revision_token_conservation.py` | upstream mutation tests; held-out measurement set | Semantic authorization still requires reviewer judgment |
| Evidence-bound revision authority | Evidence rows replay against explicit source bytes; revision roadmaps remain non-ranking proposals and exact changes require a separate author adjudication | Full-runtime handoffs carry the source-bound rows, roadmap, author-adjudication sidecar, and Revision-Evidence Bundle without inventing author choices | near | `ars/scripts/evidence_rows.py`, `ars/scripts/revision_roadmap.py`, `ars/scripts/adjudication_activity.py`, `ars/shared/handoff_schemas.md` | evidence-row, roadmap, adjudication, and integration validators | Deterministic artifacts establish traceability, not substantive correctness; activity capture is best-effort and advisory |
| Review-target and criteria binding | Review context is author-confirmed and resolved by pointer; missing venue/track context is not inferred | One manifest carries selected criteria across formative, internal, and external review without changing verdicts or editorial arithmetic | near | `ars/scripts/resolve_review_target_context.py`, `ars/scripts/review_criteria_binding.py`, `ars/academic-pipeline/references/two_stage_review_protocol.md` | review-target and criteria-binding validators | The shipped registry has a field-general baseline; venue-specific authority can remain unresolved or stale |
| Human-subjects authority | Review-ethics and data-protection profiles resolve independently from exact authority pointers; unresolved applicability blocks profile-dependent output | Traces remain institution-owned navigation aids and never become review-board decisions, authorization, readiness, or legal advice | near | `ars/scripts/resolve_human_subjects_authority.py`, `ars/scripts/build_review_pathway_rule_trace.py`, `ars/shared/references/irb_terminology_glossary.md` | human-subjects schema, output-contract, pathway, and migration validators | Institutional determination and current local authority still require the responsible human institution |
| Bibliographic and preregistration advisories | Bibliographic/retraction signals preserve provenance, disagreement, staleness, and degradation; preregistration consistency is replay-bound and nonblocking | Carriers travel as advisories without replacing citation-finalizer policy or rewriting documents | near | `ars/scripts/bibliographic_integrity_signals.py`, `ars/scripts/retraction_status.py`, `ars/scripts/build_cross_document_consistency_advisory.py` | bibliographic, retraction, and cross-document consistency tests | These artifacts are not clean-document certificates, agreement findings, or evidence of classifier/advisory efficacy |
| Citation / claim / temporal integrity | Vendored validators preserve high-impact-first claim sampling plus advisory scope and novelty rows | Planner surfaces relevant gates in the route plan | near | `ars/academic-pipeline/references/claim_verification_protocol.md`, `ars/scripts/*claim*`, `ars/scripts/temporal_integrity_audit.py`, `codex/full-runtime-manifest.json` | upstream validators; adapter tests | External metadata/API checks require configuration |
| Cross-model verification | Disabled by default; explicit provider/content/cost consent is required. Stage 2.5/4.5 one-reference citation checks may explicitly select the contained ChatGPT-subscription Codex transport | Canonical handoffs, the fixed Reviewer 2 seat, and the re-review judge pass retain dispatcher-owned provider transport; the Codex selector is citation-only and never widens to those calls | near | `README.md`, `SKILL.md`, `ars/shared/cross_model_verification.md`, `ars/scripts/cross_model_handoff.py`, `ars/scripts/cross_model_codex_transport.py` | hermetic handoff/contract and fake app-server tests; manual consent-bound live smoke only | Provider APIs require user credentials; contained citation transport requires Codex CLI 0.147.0+, `ARS_CROSS_MODEL`, the exact ChatGPT-subscription login attestation, and has no automatic API fallback |
| Codex transport post-terminal drain | A `turn/completed` event is provisional until the parent exits cleanly and stdout/stderr reach EOF; late events remain subject to all protocol and grounding checks | Same closed acceptance boundary applies when the citation transport is invoked from a planned Stage 2.5/4.5 gate | near | `ars/scripts/cross_model_codex_transport.py`, `ars/scripts/test_cross_model_codex_transport.py` | hermetic late-event, hang/reap, cap, malformed, nonzero-exit, and stderr fixtures | Drain timeout, reader failure, or a late forbidden event makes the transport visibly unavailable rather than accepting a partial result |
| Degradation provenance | Machine-readable registry records each graceful-degradation mechanism and its downstream effect | Planner exposes the registry checker as an integrity gate | near | `ars/shared/contracts/degradation_registry.json`, `ars/scripts/check_degradation_registry.py` | upstream registry tests | Runtime outages still require honest reporting to the user |
| Pipeline terminal semantics | Stage 5 entry/completion and Stage 6 decline/terminal acknowledgement follow the pinned upstream contract | Planner exposes the whole-file boundary lock | near | `ars/academic-pipeline/WORKFLOW.md`, `ars/scripts/check_pipeline_boundary_semantics.py` | upstream boundary tests | Interactive clients may express acknowledgement with different natural language |
| Upstream lock provenance | `manifest.json` pins upstream commits | Quality gate checks the package manifest has a full upstream SHA and required included paths | near | `manifest.json`, `codex/scripts/ars_codex_quality_gates.py` | `upstream-lock` gate | Future upstream syncs still require deliberate manifest updates |

## Exact Degradations Relative To Claude Code

- Codex does not register native Claude slash commands; `ars-*` aliases are
  parsed by the root skill and optional full-runtime planner.
- Codex full-runtime agent-team mode is opt-in and planner/template based.
  Inline execution remains the default.
- ARS-Codex has its own native Codex marketplace package; Claude-specific
  plugin commands, slash-command registration, and hook lifecycle are not reproduced.
- Claude Code `SessionStart` and future `SubagentStop` hooks are not installed
  automatically. The v3.18 update reminder therefore remains inactive; the
  Codex hook pack is manual and read-only.
- Heavy routes inherit the active Codex session model; light-route `sonnet`
  frontmatter is preserved as metadata. Neither changes the model unless the
  user/runtime explicitly overrides it.
- `ARS_MODEL_TIERING` preserves the upstream agent classification, but cannot
  force economy or quality-boost routing without a runtime model override.
- External cross-model verification is never simulated silently.
- The fixed Reviewer 2 track and Priority-1 re-review judge pass require an
  external provider plus explicit content consent; otherwise the required
  single-family or fallback disclosure is emitted.
- Dispatched owner roles do not perform cross-model transport themselves; the
  dispatching Codex context validates the canonical envelope and transports
  only its payload after the existing consent gate.
- The contained Codex citation transport is an explicit citation-only selector,
  requires Codex CLI 0.147.0+, `ARS_CROSS_MODEL`, the exact
  `Logged in using ChatGPT` attestation, and content/cost consent; it never
  falls back automatically to an API or expands to reviewer calls.
- Optional PDF content classification requires the separately pinned dependency.
  Its output remains an advisory with `STRUCTURE_ONLY` verdict scope; dependency
  absence is visible and cannot be promoted to structural `PASS`.
- Source-bound evidence rows, author-adjudication records, review-target
  bindings, human-subjects traces, and bibliographic/preregistration carriers
  provide deterministic provenance, not author choices, institutional approval,
  legal advice, integrity verdicts, or clean-document certificates.
- The citation transport does not accept on `turn/completed` alone. It drains
  through clean process exit and both output EOFs, so late malformed or
  forbidden events can still fail the run visibly.
