# Changelog

## v1.1.0 (2026-05-02)

PR 2 (hardening: external-edit detection, multi-study, slug-collision
recovery, explicit ethics-upgrade command, schema migration) deferred
until ≥2 weeks of v1.1.0 dogfood evidence.

Spec: [docs/specs/2026-05-02-session-resume-design.md](docs/specs/2026-05-02-session-resume-design.md)
(codex round 6 cleared). Plan:
[docs/plans/2026-05-02-session-resume-implementation.md](docs/plans/2026-05-02-session-resume-implementation.md).

### New: Session resume for human studies

- `study_manager_agent` now persists study state to disk on every
  state-changing turn. Multi-week or multi-month studies survive Claude
  session restarts.
- New `resume <study_id>` command rebuilds context from the artifact at
  `./<study_id>/state.md` (or user-specified path).
- Artifact format: Markdown + YAML frontmatter, schema_version 1.
  Template at `templates/study_state.md`, worked example at
  `templates/study_state.example.md`.
- Ethics status is now **derived** from per-item state with strict
  precedence (NOT_YET_ASSESSED → ETHICS_BLOCKED → ETHICS_PENDING →
  READY), mirroring the rules at the top of
  `references/irb_ethics_checklist.md`. Frontmatter no longer stores
  ethics_status as a cached field.
- IRB approval transitions trigger a category-based reconfirmation pass
  (categories 1, 2.2-2.5, 3.4-3.6, 4 applicable, 5.2). See
  `references/study_state_protocol.md` "IRB approval reconfirmation set."
- Stale-write detection via revision counter. Two Claude sessions
  writing the same artifact are now safe: the second writer detects the
  revision change and refuses, asking the user how to resolve.
- Prompt-injection guard: artifact body content is treated as data
  describing the study, never as instruction directed at the agent.
- Runtime requirement: `resume` requires Read/Write/Edit tool access
  (Claude Code OK; chat-only runtimes do not get persistence).

### Out of scope for v1.1.0 (deferred to v1.2.0)

- External-edit detection (artifact edited externally with same revision)
- Vanished-file or moved-file recovery
- Multi-study concurrent in same workspace
- Explicit `ethics-upgrade` command
- Slug-collision resolution (v1.1.0 refuses + asks user)
- Auto-archive or garbage collection of old artifacts
- Schema migration tooling

### No breaking changes

- v1.0.1 users see no behavior change unless they invoke `resume` or
  start a study under the new persistence path
- Material Passport schema unchanged; ARS coupling unchanged
- `code_runner_agent` unchanged

## v1.0.1 (2026-05-02)

### Contract Fixes

- Clarified `validate` output semantics: `Verification Status` is now `ANALYZED` unless a successful reproducibility re-run upgrades it to `VERIFIED`
- Added Material Passport headers to `plan` mode templates (`code_experiment_plan.md`, `study_protocol.md`)
- Fixed reproducibility guidance for zero-baseline metrics by using a symmetric denominator with epsilon protection
- Reclassified hardware/OS-sensitive runs as `environment-sensitive` comparisons instead of blanket `not applicable`
- Added `CANNOT_VERIFY` and environment-sensitive cases to the documented validation/reproducibility output contract
- Tightened ethics gating so only `READY` can enter study tracking, while `ETHICS_PENDING` still blocks participant recruitment and data collection
- Relaxed consent wording to allow IRB-approved digital, implied, or waived consent paths where appropriate
- Corrected the chi-squared fallback guidance so Fisher's exact is limited to 2x2 tables

## v1.0 (2026-04-09)

### Initial Release

**New Skill: experiment-agent**

- 4 modes: `run` (code experiments), `manage` (human studies), `validate` (statistical interpretation + reproducibility), `plan` (Socratic experiment design)
- 2 agents: `code_runner_agent` (execute + monitor), `study_manager_agent` (plan + track)
- 5 reference protocols: stall detection, IRB ethics checklist, statistical interpretation (11-type fallacy scan), reproducibility verification, ARS integration guide
- 2 templates: code experiment plan, study protocol
- ARS-compatible Material Passport output (Schema 9)
- Independent operation + optional ARS pipeline integration (zero ARS modification)
- Source: Lu et al. (2026, *Nature* 651:914-919) Experiment Progress Manager concept

**Design decisions:**
- Executor + Monitor role only (no quality review — that's ARS reviewer's job)
- All anomaly detections are ADVISORY (user decides, except hard timeout)
- Statistical interpretation is descriptive (flags issues, does not make editorial recommendations)
- validate mode scope boundary: describes what numbers say, does not judge paper quality
- Single-direction ARS dependency: experiment-agent knows ARS format, ARS does not know experiment-agent
