# Codex Full-Runtime Adapter Guide

This guide documents the optional full-runtime profile for
`academic-research-suite`. The default ARS Codex behavior remains inline
role-prompt execution through `skills/academic-research-suite/SKILL.md`.

## What This Adds

The Codex-only adapter lives under `skills/academic-research-suite/codex/` and
adds four pieces:

1. `full-runtime-manifest.json` defines alias routing, workflow mapping,
   agent-team rules, hook metadata, quality gates, and known degradations.
2. `agents/*.md` defines Codex agent-team templates for deep research,
   academic paper writing, academic pipeline orchestration, paper review, and
   experiment planning.
3. `scripts/ars_codex_full_runtime.py` produces deterministic JSON route plans.
   It is read-only and does not spawn agents or execute hooks.
4. `hooks/` contains a disabled-by-default read-only hook pack. It must be
   manually installed and explicitly enabled before use.

The vendored upstream ARS content remains under
`skills/academic-research-suite/ars/`. The current package manifest pins the
exact upstream commit.

## Enablement

No environment variables are required for normal ARS Codex use.

Enable full-runtime planning:

```bash
export ARS_CODEX_FULL_RUNTIME=1
```

Enable planner-driven Codex agent-team dispatch:

```bash
export ARS_CODEX_AGENT_TEAM=1
```

Enable the hook pack:

```bash
export ARS_CODEX_HOOKS=1
```

Recommended opt-in profile:

```bash
export ARS_CODEX_FULL_RUNTIME=1
export ARS_CODEX_AGENT_TEAM=1
```

Hooks still require explicit manual installation or a Codex hook configuration
that references `skills/academic-research-suite/codex/hooks/hooks.json`.

## Usage

Default inline usage:

```text
Use $academic-research-suite. ars-plan Research question: How do quality assurance agencies evaluate AI governance in universities?
```

Planner inspection:

```bash
ARS_CODEX_FULL_RUNTIME=1 ARS_CODEX_AGENT_TEAM=1 \
python3 skills/academic-research-suite/codex/scripts/ars_codex_full_runtime.py --pretty \
  "ars-reviewer full review for this manuscript."
```

## Verification

Run adapter gates from the repository root:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all
```

Run adapter tests:

```bash
python3 -m pytest skills/academic-research-suite/codex/tests -q
```

## Known Degradations

- Codex does not register Claude Code slash commands. ARS aliases are parsed by
  the root skill and optional planner.
- Codex agent-team behavior is opt-in and runtime-dependent. Inline execution
  remains the default.
- Claude Code plugin marketplace install/update is not reproduced.
- Hook installation is manual and disabled by default.
- Claude `opus` / `sonnet` model hints are preserved as metadata; Codex uses the
  active model unless a user or runtime explicitly overrides it.
- External cross-model verification is never silently simulated.
