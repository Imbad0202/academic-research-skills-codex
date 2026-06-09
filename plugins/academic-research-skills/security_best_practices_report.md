# ARS Codex Release Readiness And Security Report

Date: 2026-05-10

Scope: `skills/academic-research-suite` in `academic-research-skills-codex`.
The upstream `academic-research-skills` checkout was not modified.

## Summary

- E2E audit wrapper: PASS, `3 passed`.
- Full pytest suite: PASS, `901 passed`.
- Python syntax: PASS, `compileall` completed.
- Shell syntax: PASS, `bash -n` completed for shipped shell scripts.
- JSON validation: PASS for `manifest.json` and vendored `hooks/hooks.json`.
- Dependency CVE scan: PASS, `pip-audit` reported no known vulnerabilities.
- SAST high/medium gate: PASS, Bandit reported no high or medium severity issues.
- Secret scan: PASS after triage; no verified secrets found.

## Fixes Applied During Readiness Testing

- Relaxed `scripts/run_codex_audit.sh` from Bash 4+ to Bash 3.2+ because the Codex adapter only uses Bash 3.2-compatible features. This makes the e2e runnable on stock macOS Bash.
- Updated `scripts/test_run_codex_audit_e2e.py` to run on Bash 3.2+ instead of skipping macOS.
- Fixed nested vendoring in `check_audit_artifact_consistency.py` B4 git-SHA validation by asking Git for the repo top-level instead of requiring `repo_root/.git`.
- Made direct-exec smoke test prefer the active pytest interpreter directory in `PATH`, avoiding macOS `/usr/bin/env python3` picking a different Python without dev dependencies.
- Replaced API-key-shaped documentation placeholders with neutral placeholders.
- Added precise `# nosec B506` annotations for PyYAML loads that use `BaseLoader` or a `SafeLoader` subclass.
- Updated v3.6.7 mutation tests to copy the active Codex working tree instead of stale `HEAD`, preserving mutation coverage before the initial vendor commit exists.
- Added `scripts/codex_v3_6_7_block_baseline.json`, a Codex-specific first-vendor SHA baseline for the three v3.6.7 PATTERN PROTECTION blocks. `check_v3_6_8_pattern_protection.py` uses it only when Git history cannot derive the upstream v3.6.7 baseline.

## Remaining Release Blockers

None found in this pass. The prior 67 failures were resolved by Codex working-tree mutation testing and the vendored v3.6.7 block baseline.

## Security Results

- `bandit -lll -ii`: no issues identified.
- Full Bandit JSON after triage: `0 high`, `0 medium`, `17 low`; lows are subprocess usage with argument arrays, hardcoded non-secret tokens/regexes, and a catch/pass in validation fallback code.
- `pip-audit --path /private/tmp/ars-runtime-deps`: no known vulnerabilities found.
- `detect-secrets scan`: no verified secrets. Remaining hits are commit SHAs, fixture SHA-256 values, and test/design hex constants.
- Manual high-risk scan found no `shell=True`, `eval()`, `exec()`, `os.system()`, private keys, or real API keys.

## Other Checks

- `scripts/test_run_codex_audit_e2e.py -q`: `3 passed`.
- `scripts/test_check_audit_artifact_consistency.py -q`: `135 passed`.
- `scripts/test_check_v3_6_7_pattern_protection.py -q`: `58 passed`.
- `scripts/test_check_v3_6_8_pattern_protection.py -q`: `45 passed`.
- `python -m pytest --tb=short -q`: `901 passed`.
- `python -m json.tool skills/academic-research-suite/manifest.json`: passed.
- `python -m json.tool skills/academic-research-suite/ars/scripts/codex_v3_6_7_block_baseline.json`: passed.
- `python -m json.tool skills/academic-research-suite/ars/hooks/hooks.json`: passed.
- `find skills/academic-research-suite/ars -type l`: no symlinks found.
- `find skills/academic-research-suite/ars -type f -size +5M`: no files over 5 MB found.

## Recommendation

No security blocker was found. The package is release-green on the local readiness suite run above; keep the Codex vendored baseline in sync whenever the v3.6.7 protected blocks are intentionally amended.
