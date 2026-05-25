# Changelog

All notable changes to the Codex package are documented here.

## [0.2.0] - 2026-05-25

### Added
- Added the opt-in Codex full-runtime adapter under
  `skills/academic-research-suite/codex/`, including command routing,
  agent-team templates, hook safety metadata, a deterministic runtime planner,
  adapter quality gates, parity tests, and a compatibility matrix.
- Added `ars-reviewer`, `ars-mark-read`, and `ars-unmark-read` alias coverage
  through the root router and full-runtime manifest.
- Added reviewer independence and synthesis-preservation checks for full
  paper-reviewer mode.

### Changed
- Synced vendored upstream ARS content from
  `96b82e82142dc95f117595c207d3e150b078e411` to
  `cb2f4e07019e1cd72881547e91d880ec7cc0d7fc`, excluding Claude loader files,
  symlink-only alias directories, `.github`, `.git`, and showcase PDFs.
- Kept inline mode as the default; full-runtime, agent-team, and hook behavior
  require explicit opt-in environment flags.

### Notes
- Codex still does not provide native Claude Code plugin lifecycle, slash
  command registration, hook execution, or `opus` / `sonnet` model pinning.
  These are documented as degraded behavior in the compatibility matrix.

## [0.1.8] - 2026-05-19

### Changed
- Vendored upstream ARS from `74413a42571867abece7b8b76f7a24ac472ab2a0` (`v3.9.0`) to `96b82e82142dc95f117595c207d3e150b078e411` (`v3.9.4.2`).
- Added ARS v3.9.1 client hardening, v3.9.2 phase-boundary routing discipline, v3.9.3 shared client utilities, and v3.9.4/v3.9.4.1 temporal verification runtime content.
- Kept Codex-specific overlays: single root router skill, `WORKFLOW.md` vendored workflow entry files, Codex setup/architecture docs, nested-path lint patches, and macOS Bash 3.2 audit wrapper compatibility.

### Notes
- Upstream v3.9.4.2 changes only `.github` CI/release-gate files, which are intentionally excluded from this Codex package. The manifest still pins the exact v3.9.4.2 commit for provenance.

## [0.1.7] - 2026-05-17

### Changed
- Aligned the Codex package with upstream ARS `v3.9.0`.
