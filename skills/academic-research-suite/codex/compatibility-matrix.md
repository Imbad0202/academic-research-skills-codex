# ARS Codex Compatibility Matrix

Audit date: 2026-05-25

## Provenance

| Surface | Evidence |
|---|---|
| Codex package repo | `academic-research-skills-codex` at `900238ce1b04109bc3e11a4849f4be55122e5301` before this adapter work |
| Upstream Claude Code repo | `academic-research-skills` at `cb2f4e07019e1cd72881547e91d880ec7cc0d7fc` (`origin/main`, no tag on HEAD during audit) |
| Upstream suite version | `3.9.4.2` in `.claude-plugin/plugin.json` and `.claude/CLAUDE.md`; tag `v3.9.4.2` points to `96b82e82142dc95f117595c207d3e150b078e411` |
| Codex adapter version | `0.2.0` after this work |
| License | CC BY-NC 4.0 in upstream and Codex package |
| Upstream sync status | Vendored `ars/` content synced from `academic-research-skills@cb2f4e0`, excluding Claude loader directories, symlink-only skill/agent aliases, `.github`, `.git`, and showcase PDFs |
| Codex-only adapter location | `skills/academic-research-suite/codex/` |

## Matrix

| CC capability | Current Codex status | Target Codex implementation | Parity level | Implementation location | Verification method | Remaining risk |
|---|---|---|---|---|---|---|
| Plugin lifecycle / install / update via `.claude-plugin` marketplace | Codex installs one skill path, not a Claude plugin | Keep single Codex skill install; record upstream plugin metadata as provenance; update by reinstalling the Codex skill or pulling this repo | partial | `README.md`, `skills/academic-research-suite/manifest.json` | local install command; `/skills`; `single-root-skill` gate | No native Codex marketplace lifecycle equivalent |
| `/ars-*` commands / aliases | Prior Codex router covered 10 aliases; upstream now has 13 including reviewer and mark-read commands | Route all 13 aliases through root router and deterministic full-runtime planner | near | `SKILL.md`, `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py`, `ars/commands/*.md` | pytest `test_full_runtime_adapter.py`; manifest gate | Slash-prefixed input can still be intercepted by client; plain aliases remain fallback |
| Routing discipline | Prior router had vague-topic Socratic override but no full-runtime planner | Deterministic planner preserves vague paper-topic override, alias routing, checkpoint stop detection, and full-runtime degradation reporting | near | `SKILL.md`, `codex/scripts/ars_codex_full_runtime.py` | pytest route tests; upstream `scripts/test_codex_router_policy.py` | Natural-language routing remains heuristic outside covered smoke cases |
| `MODE_REGISTRY.md` | Vendored registry was pinned to older upstream commit | Sync current upstream registry and keep planner modes aligned with manifest | near | `ars/MODE_REGISTRY.md`, `codex/full-runtime-manifest.json` | manifest gate; upstream version/spec validators where active | Future upstream mode additions require sync |
| Commands | Command recipes vendored as prompt recipes, not native Codex commands | Vendored current command recipes and expose deterministic alias metadata | near | `ars/commands/*.md`, `codex/full-runtime-manifest.json` | manifest gate checks recipes exist | Mark-read still needs an active passport path supplied by session context |
| Agents | Prior Codex mode used agent markdown inline only | Add opt-in Codex agent-team templates that reference upstream prompts and preserve inline fallback | near | `codex/agents/*.md`, `codex/full-runtime-manifest.json` | manifest gate; reviewer agent-team pytest | Codex subagent availability is runtime-dependent; planner does not spawn by itself |
| Hooks | Upstream Claude `SessionStart` hook vendored only as metadata | Add disabled-by-default Codex hook pack with read-only wrapper and static safety gate | partial | `codex/hooks/hooks.json`, `codex/scripts/ars_codex_hook.py`, `codex/scripts/ars_codex_quality_gates.py` | `hook-safety` gate | Codex hook installation format can differ by client; manual install remains required |
| Model routing (`opus` / `sonnet`) | Previously documented as Claude metadata only | Preserve command model hints in planner output while using active Codex model unless user/runtime overrides | partial | `codex/full-runtime-manifest.json`, `codex/scripts/ars_codex_full_runtime.py` | pytest alias route asserts `model_hint`; manual plan inspection | Not equivalent to Claude Code model pinning |
| Workflow routing | Single root skill selects vendored `WORKFLOW.md` files | Keep single root router; full-runtime planner emits workflow path and mode for every command/natural route | near | `SKILL.md`, `codex/scripts/ars_codex_full_runtime.py` | `single-root-skill`; pytest planner tests | Complex cross-phase ambiguity still may need human clarification |
| Material Passport / reset semantics | Upstream scripts and docs vendored; Codex maps fresh Claude session to fresh Codex conversation | Sync latest upstream passport scripts; full-runtime manifest includes passport reset gate | near | `ars/scripts/check_passport_reset_contract.py`, `ars/academic-pipeline/references/passport_as_reset_boundary.md`, `codex/full-runtime-manifest.json` | upstream passport validator; adapter quality gate lock | Runtime reset boundaries are prompt/procedure plus artifact validation, not enforced context isolation |
| Citation verification / claim audit / integrity gates | Upstream scripts vendored; Codex default uses prompt discipline plus validators when run | Keep upstream validators and expose them as quality gates; full-runtime planner reports relevant gates | partial | `ars/scripts/*claim*`, `ars/scripts/temporal_integrity_audit.py`, `codex/full-runtime-manifest.json` | upstream pytest/validators; adapter `manifest` gate | LLM-as-judge and external metadata checks require configured sources/API and cannot be fully deterministic |
| Cross-model verification | Upstream supports optional secondary-model checks; Codex prior docs disabled by default | Keep disabled by default; require explicit configuration and report unavailable verifier instead of inventing results | partial | `SKILL.md`, `README.md`, `codex/full-runtime-manifest.json` | manual plan/review inspection | No guaranteed parity with upstream GPT/Gemini/Claude secondary dispatch |
| Reviewer independence and synthesis | Upstream reviewer full mode relies on Agent Team and sprint contract | Codex agent-team template and planner enforce independent reviewer sections before editorial synthesis, with minority/dissent retention | near | `codex/agents/paper-reviewer-panel.md`, `codex/tests/fixtures/reviewer_full_independent_sections.md`, `codex/scripts/ars_codex_quality_gates.py` | reviewer fixture gate; pytest reviewer plan test | Actual independence depends on using subagents or faithfully following inline section boundary |
| Scripts / validators / tests | Codex had many upstream validators but was behind current upstream after `v3.9.4.2` tag | Sync current upstream scripts/tests and add adapter smoke/parity tests | near | `ars/scripts/`, `ars/tests/`, `codex/tests/` | pytest adapter tests; selected upstream validators | Some upstream validators depend on non-vendored Claude files and remain inactive by manifest |
| Upstream sync / lockfile provenance | Manifest pinned `96b82e8` while upstream HEAD was `cb2f4e0` | Update manifest lock to `cb2f4e0`; gate rejects stale lock | near | `skills/academic-research-suite/manifest.json`, `codex/scripts/ars_codex_quality_gates.py` | `upstream-lock` gate | Future upstream changes need explicit sync and lock update |

## Exact Degradations Relative To Claude Code

- Codex does not register native Claude slash commands; `ars-*` aliases are
  parsed by the root skill and full-runtime planner.
- Codex full-runtime agent-team mode is opt-in and planner/template based.
  Inline execution remains the default.
- Claude Code plugin marketplace install/update is not reproduced.
- Claude Code `SessionStart` and future `SubagentStop` hooks are not installed
  automatically. The Codex hook pack is manual and read-only.
- `opus` / `sonnet` command frontmatter is preserved as metadata; the active
  Codex model is used unless the user/runtime provides an explicit override.
- External cross-model verification is never simulated silently.
