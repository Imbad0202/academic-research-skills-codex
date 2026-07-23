# ARS-Codex Compatibility Matrix

Audit date: 2026-07-22

## Provenance

| Surface | Evidence |
|---|---|
| Codex package repo | `academic-research-skills-codex` current working tree before release commit |
| Upstream Claude Code repo | Tracked in `skills/academic-research-suite/manifest.json` |
| Upstream suite version | `v3.19.0` |
| Codex package version | `0.1.22` |
| License | CC BY-NC 4.0 in upstream and Codex package |
| Upstream sync status | Vendored `ars/` content synced to ARS release `v3.19.0` (`828ef3b`); Codex adapter profile retained |
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
| Model routing | Claude `opus` / `sonnet` hints are metadata | Planner reports model hints without forcing model changes | partial | `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | adapter pytest; plan inspection | Not equivalent to Claude Code model pinning |
| ARS model tiering | Unset preserves the active Codex model | Planner surfaces `economy` / `quality-boost` as advisory metadata; classification is applied only when per-dispatch model selection exists | partial | `ars/shared/model_tiering.md`, `ars/scripts/model_tiering_manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | upstream tiering lint; adapter pytest | Codex runtimes may not expose relative-tier or per-dispatch model control |
| Material Passport | Prompt/procedure plus vendored validators | Full-runtime manifest exposes passport reset as a quality gate | near | `ars/scripts/check_passport_reset_contract.py`, `codex/full-runtime-manifest.json` | upstream validator; adapter gate | Runtime context isolation is procedural, not a hard sandbox |
| Citation cache staleness and re-validation | Cached verification remains the default; stale rows are advisory-only | Planner surfaces the threshold and whether live re-validation was requested | near | `ars/scripts/verification_cache.py`, `ars/scripts/verification_gate/`, `codex/scripts/ars_codex_full_runtime.py` | upstream cache/gate tests; adapter pytest | Live re-validation depends on external bibliographic services |
| Local-PDF read integrity | Locally read PDFs receive the pypdf-backed preflight before page anchors are trusted | Planner contract requires Stage 1 sidecars, freshness checks, and distinct FAIL/UNAVAILABLE handling | near | `ars/scripts/pdf_read_preflight.py`, `ars/academic-pipeline/agents/pipeline_orchestrator_agent.md` | upstream preflight tests; boundary validator | Missing pypdf produces an explicit advisory and cannot establish PASS |
| Human-read scope | Optional `read_scope` is written only from user declarations; partial coverage remains visible | Orchestrator contract carries ledger scope into finalizer decisions | near | `ars/scripts/ars_mark_read.py`, `ars/shared/contracts/passport/human_read_log.schema.json` | upstream mark-read and finalizer tests | Legacy marks without scope intentionally resolve as unknown |
| Revision claim-drift guards | Claim-strength changes and conserved tokens are checked advisory-first for every revision round | Planner contract carries the Revision-Evidence Bundle across rounds | near | `ars/shared/references/claim_strength_ladder.md`, `ars/scripts/check_revision_token_conservation.py` | upstream mutation tests; held-out measurement set | Semantic authorization still requires reviewer judgment |
| Citation / claim / temporal integrity | Vendored validators preserve high-impact-first claim sampling plus advisory scope and novelty rows | Planner surfaces relevant gates in the route plan | near | `ars/academic-pipeline/references/claim_verification_protocol.md`, `ars/scripts/*claim*`, `ars/scripts/temporal_integrity_audit.py`, `codex/full-runtime-manifest.json` | upstream validators; adapter tests | External metadata/API checks require configuration |
| Cross-model verification | Disabled by default; explicit provider configuration and user consent required | Canonical handoffs, the fixed Reviewer 2 seat, and the re-review judge pass use dispatcher-owned transport with provenance/fallback disclosure | near | `README.md`, `SKILL.md`, `ars/shared/cross_model_verification.md`, `ars/scripts/cross_model_handoff.py`, `codex/agents/paper-reviewer-panel.md` | hermetic handoff/contract tests; adapter pytest | External-provider availability depends on user-supplied API credentials |
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
- `opus` / `sonnet` command frontmatter is preserved as metadata; the active
  Codex model is used unless the user/runtime provides an explicit override.
- `ARS_MODEL_TIERING` preserves the upstream agent classification, but cannot
  force economy or quality-boost routing without a runtime model override.
- External cross-model verification is never simulated silently.
- The fixed Reviewer 2 track and Priority-1 re-review judge pass require an
  external provider plus explicit content consent; otherwise the required
  single-family or fallback disclosure is emitted.
- Dispatched owner roles do not perform cross-model transport themselves; the
  dispatching Codex context validates the canonical envelope and transports
  only its payload after the existing consent gate.
