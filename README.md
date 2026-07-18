# ARS-Codex

[![Version](https://img.shields.io/badge/version-v0.1.21-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

ARS-Codex is the Codex-native sibling of
[Academic Research Skills (ARS) for Claude Code](https://github.com/Imbad0202/academic-research-skills).
It is a separate Codex distribution with its own plugin identity, packaging,
versioning, and runtime adapter.

This repository vendors the ARS workflow content as a single Codex skill:

```text
skills/academic-research-suite/
  SKILL.md
  manifest.json
  agents/openai.yaml
  codex/
    full-runtime-manifest.json
    agents/
    hooks/
    scripts/
  ars/
    deep-research/
    academic-paper/
    academic-paper-reviewer/
    academic-pipeline/
    experiment-agent/
    commands/
    hooks/
    docs/
    tests/
    shared/
```

The original Claude Code ARS checkout is not modified. Upstream content is copied
from fresh GitHub clones and adapted through the Codex router in
`skills/academic-research-suite/SKILL.md`.

## Relationship to Claude Code ARS

This repository is ARS-Codex. For the original Claude Code ARS distribution, use
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills).

Use the Claude Code repo when you want the native Claude Code skill layout,
Claude-specific agent-team behavior, or the original ARS development history.
Use this repo when you want the Codex-native single-suite skill.

## Versioning

This ARS-Codex package is version `0.1.21`. The repo-root `VERSION` file,
`skills/academic-research-suite/SKILL.md` metadata version, and
`skills/academic-research-suite/manifest.json` `adapter_version` track the
Codex package version independently of the vendored ARS suite. Vendored upstream
versions are recorded by commit in `manifest.source_repositories[]`.

Package-level changes are summarized in [`CHANGELOG.md`](CHANGELOG.md).

The vendored ARS source currently tracks
`Imbad0202/academic-research-skills@bbc0659272a511b422f6856cd6f44b6ccb2ac213`
(`v3.18.0`). Vendored runtime content includes the fixed-seat cross-model
Reviewer 2 track and re-review Judge Record, citation-cache staleness advisories
with opt-in live re-validation, high-impact-first claim sampling,
scope-conformance and search-bounded novelty advisories, and the held-out
pipeline-behavior robustness set. The v3.17 dispatcher, least-privilege,
panel-synthesis, degradation-registry, boundary-lock, and hermetic transport
contracts remain intact.
Nested upstream `.github/` workflows and root `agents/` mirrors are preserved
for traceability and self-tests, but are not repo-level CI or Codex entrypoints;
Claude/plugin loader files under `.claude/` and `.claude-plugin/` remain
intentionally excluded.

## Install ARS-Codex Plugin

Add the GitHub marketplace and install ARS-Codex with Codex CLI:

```bash
codex plugin marketplace add Imbad0202/academic-research-skills-codex --ref main
codex plugin add ars-codex@ars-codex
```

To update a plugin install later:

```bash
codex plugin marketplace upgrade ars-codex
codex plugin add ars-codex@ars-codex
```

In Codex Desktop, you can alternatively add the repository from **Plugins** and
then install **ARS-Codex**:

```text
Marketplace source: https://github.com/Imbad0202/academic-research-skills-codex.git
Branch/ref: main
Plugin: ars-codex
```

The plugin root is `plugins/ars-codex/`. Its `skills/` directory contains a
materialized copy of `academic-research-suite`, not a symlink. This keeps
Codex Desktop installs portable on Windows, where plugin caches may materialize
symlinks as plain text files and skip bundled skill registration.

Open a new Codex conversation after installation, then invoke
`$academic-research-suite` or describe an academic research task that matches
the bundled workflow.

## Direct Skill Install Or Update

As an alternative to the plugin, install the skill directly from this repo
path. Use `--method git` so public and
credentialed GitHub access both work consistently:

```bash
python3 "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

On macOS and many Linux systems, Python 3 is exposed as `python3` rather than
`python`. If your system only has a `python` command and it is Python 3, use
`python` in the commands instead.

To update an existing install:

```bash
rm -rf "$HOME/.codex/skills/academic-research-suite"
python3 "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

Open a new Codex conversation after installation. Existing Codex sessions may
keep their old skill cache; you do not need to close unrelated Claude or Codex
sessions.

Verify with `/skills`: you should see one ARS-Codex entry,
`academic-research-suite` or `ARS-Codex`. You should **not** see separate `academic-paper`,
`academic-pipeline`, `deep-research`, or `academic-paper-reviewer` skills from
this package. If you do, reinstall with the update command above and open a new
Codex conversation.

## Codex Docs

- [Codex setup](skills/academic-research-suite/ars/docs/SETUP.md) covers
  installation, `ars-*` aliases, optional tools, Material Passport adapters,
  and unsupported Claude plugin features.
- [Codex architecture](skills/academic-research-suite/ars/docs/ARCHITECTURE.md)
  explains the logical ARS pipeline with the Codex runtime overlay.
- [Optional full-runtime adapter](CODEX_FULL_RUNTIME_ADAPTER.md) documents the
  disabled-by-default planner, Codex agent-team templates, and hook pack.

## Usage

Invoke the suite explicitly with `$academic-research-suite` (singular), then
describe the research task and provide any source files, notes, draft text,
reviewer comments, or output constraints.

```text
Use $academic-research-suite to help me plan a systematic literature review on
AI adoption in higher education quality assurance.
```

The Codex adapter routes the request to one of five ARS workflows:

| Workflow | Use when you need | Example prompt |
|---|---|---|
| `deep-research` | Research question refinement, literature review, systematic review, meta-analysis, fact-checking | `Use $academic-research-suite to build a systematic review protocol for AI in higher education QA.` |
| `academic-paper` | Paper outline, drafting, abstract, revision, citation formatting, AI disclosure | `Use $academic-research-suite to turn these notes into an IMRaD paper outline and drafting plan.` |
| `academic-paper-reviewer` | Manuscript review, simulated peer review, editorial decision, re-review | `Use $academic-research-suite to review this manuscript and produce a journal-style decision letter.` |
| `academic-pipeline` | End-to-end research-to-paper workflow with integrity gates, review, revision, and final checks | `Use $academic-research-suite to run an end-to-end research-to-paper pipeline from topic to revised manuscript.` |
| `experiment-agent` | Code experiment planning, human study protocol, statistical interpretation, reproducibility validation | `Use $academic-research-suite to plan a code experiment and define reproducibility checks.` |

### Claude-Style Aliases

Claude Code v3.7 installs `/ars-*` slash commands. Codex does not have the same
plugin command registry, so this package emulates the command intent inside the
single `$academic-research-suite` skill. Use either form:

```text
Use $academic-research-suite: ars-plan my paper on AI governance in universities.
```

or, when your Codex client passes slash-prefixed text through as a normal user
message:

```text
/ars-plan my paper on AI governance in universities.
```

If slash input is intercepted by the client, use the plain alias form:

```text
ars-plan my paper on AI governance in universities.
```

| Claude command | Codex alias | Routed workflow |
|---|---|---|
| `/ars-plan` | `ars-plan` | `academic-paper` `plan` mode |
| `/ars-outline` | `ars-outline` | `academic-paper` `outline-only` mode |
| `/ars-abstract` | `ars-abstract` | `academic-paper` `abstract-only` mode |
| `/ars-lit-review` | `ars-lit-review` | `academic-paper` `lit-review` mode |
| `/ars-citation-check` | `ars-citation-check` | `academic-paper` `citation-check` mode |
| `/ars-disclosure` | `ars-disclosure` | `academic-paper` `disclosure` mode |
| `/ars-format-convert` | `ars-format-convert` | `academic-paper` `format-convert` mode |
| `/ars-revision-coach` | `ars-revision-coach` | `academic-paper` `revision-coach` mode |
| `/ars-revision` | `ars-revision` | `academic-paper` `revision` mode |
| `/ars-reviewer` | `ars-reviewer` | `academic-paper-reviewer` full mode |
| `/ars-mark-read` | `ars-mark-read` | Human-read signal for citation keys in the active Material Passport |
| `/ars-unmark-read` | `ars-unmark-read` | Rescind a prior human-read signal |
| `/ars-cache-invalidate` | `ars-cache-invalidate` | Invalidate cached verification entries for one citation key |
| `/ars-full` | `ars-full` | `academic-pipeline` full workflow |

### Working Pattern

For best results, start with the workflow goal and the current state of your
materials:

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: English, APA 7, higher education policy audience.
```

If you only have a paper topic or broad research direction and do not yet have a
clear research question, the Codex router should start with ARS Socratic
scoping:

```text
Use $academic-research-suite.

I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic dialogue to help me narrow the question first; do not write an outline yet.
```

Expected route: `deep-research` `socratic` mode first. ARS should ask narrowing
questions and should not produce an outline or draft until the research question
has converged.

For review tasks, provide the manuscript or a path to the manuscript, plus the
review mode you want:

```text
Use $academic-research-suite to review this paper.
Mode: full review.
Focus: methodology, contribution, citation integrity, and likely desk-reject risks.
Output: reviewer reports plus editorial decision letter.
```

For staged pipelines, ask for a checkpoint instead of asking Codex to run the
entire process silently:

```text
Use $academic-research-suite to start an academic-pipeline run.
Begin with Stage 0 intake and stop after producing the pipeline dashboard.
```

### Smoke Tests

In a new Codex conversation:

```text
/skills
```

Expected: one ARS entry only.

Then test Socratic routing:

```text
Use $academic-research-suite.
I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
```

Expected: route to `deep-research` `socratic` mode and ask narrowing questions.

CLI smoke test:

```bash
codex exec --ephemeral --sandbox read-only \
  -C /path/to/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: I want to write a paper on AI adoption in higher education quality assurance, but I do not yet have a clear research question. According to the academic-research-suite router, classify the workflow and mode.'
```

Maintainer quality gates:

```bash
python3 skills/academic-research-suite/codex/scripts/ars_codex_quality_gates.py all --json
```

Expected: every reported gate has `"ok": true`.

### Non-Blocking Codex Warnings

These Codex messages do not mean ARS failed to install:

- `[features].codex_hooks is deprecated` — update your Codex config when
  convenient; ARS-Codex does not require hooks for normal use.
- `hooks need review before they can run` — review those hooks separately if
  you use them. ARS-Codex treats vendored Claude hooks as traceability metadata
  and does not require them.

### Codex Adapter Behavior

ARS was originally written for Claude Code. In this Codex package:

- The vendored `agents/*.md` files are used as role and phase prompts.
- The Codex-only `codex/` directory contains an optional full-runtime adapter
  profile. It is disabled by default and does not change normal inline routing.
- The vendored `commands/ars-*.md` files are prompt recipes only. Codex does not
  register them as slash commands.
- The vendored `hooks/hooks.json` file is preserved for upstream traceability
  only. Codex does not install Claude Code hooks from this package.
- Codex does not automatically spawn background agents unless you explicitly ask
  for delegated or parallel agent work.
- Web/source verification uses Codex browsing and must cite sources when current
  or external facts matter.
- Cross-model verification is disabled by default. When explicitly requested in
  this Codex package, follow the vendored provider setup in
  `ars/shared/cross_model_verification.md`, identify the provider/model/content
  class first, and obtain explicit user consent before any external upload.
  External reviewers are called through configured provider APIs, not simulated
  through the active Codex model.
- `ARS_MODEL_TIERING` is unset by default. The Codex adapter preserves the
  upstream judgment/execution classification but applies `economy` or
  `quality-boost` only when the runtime supports an explicit per-dispatch model
  override; otherwise it reports a no-op and keeps the active model.
- Protected top-level agent `tools:` allowlists remain least-privilege role
  boundaries. A dispatched checkpoint owner does not gain Bash or network
  transport; the dispatching Codex context owns any explicitly consented
  cross-model call.
- A `[CROSS-MODEL-HANDOFF v1]` block is a transport request, not a deliverable.
  The dispatcher validates it, sends only its payload, applies the mechanical
  result routing, and returns judgment work to the original owner.
- In reviewer `full` mode, an explicitly configured and consented cross-model
  run swaps the existing Reviewer 2 seat; it never adds a sixth reviewer.
  Re-review applies the separate Priority-1 judge pass and records provenance.
  Single-family execution and provider fallback are disclosed.
- `ARS_CACHE_STALE_ADVISORY_DAYS` controls the advisory-only cache-age threshold,
  while `ARS_CACHE_REVALIDATE=1` opts into live bibliographic re-validation.
  These settings apply when the programmatic citation gate is run; stale rows
  alone never fail an integrity gate.
- The upstream v3.18 SessionStart update checker is vendored but not installed
  or executed as a Codex hook. Plugin users update with
  `codex plugin marketplace upgrade ars-codex` followed by
  `codex plugin add ars-codex@ars-codex`; direct skill installs still update by
  reinstalling or pulling this repository.
- Upstream references to a "fresh Claude Code session" mean a new Codex
  conversation in this package; Material Passport reset semantics still apply.
- If a citation, source, statistic, or journal policy cannot be verified, Codex
  should mark it as unverified rather than invent support.

### ARS v3.18 Release Parity

This package aims for the same user-facing workflow content as upstream ARS
`v3.18.0` where Codex has an equivalent concept.

| Upstream ARS feature | Codex package behavior |
|---|---|
| One installable plugin | Native Codex plugin `ars-codex`, bundling the single `academic-research-suite` skill |
| `/ars-*` slash commands | Emulated as `ars-*` aliases through the skill router; not native slash commands |
| Four upstream skills auto-discovered from `skills/` symlinks | Single Codex router skill selects the workflow and reads the vendored workflow `WORKFLOW.md` files |
| Plugin-shipped agents | Agent files are role/phase prompts; Codex runs them inline unless the user explicitly asks for delegated subagents |
| Optional Codex full-runtime profile | Planner, agent-team templates, and hook pack live under `skills/academic-research-suite/codex/`; disabled by default |
| `model: opus` / `model: sonnet` command routing | Treated as Claude metadata; Codex uses the active model |
| `ARS_MODEL_TIERING=economy\|quality-boost` | Classification is preserved; routing remains advisory unless Codex exposes per-dispatch model selection |
| Protected agent `tools:` allowlists | Preserved as least-privilege role boundaries; dispatched owners do not receive Bash/network transport |
| Canonical cross-model handoff envelope | Dispatcher validates the envelope, transports only the payload after consent, and follows the closed result-routing contract |
| Cross-model Reviewer 2 and re-review judge tracks | Available only with explicit provider configuration and content consent; the fixed seat, Judge Record, single-family disclosure, and fallback disclosure are preserved |
| Cache staleness advisory and live re-validation | Local cache remains the default; stale rows are advisory-only and `ARS_CACHE_REVALIDATE=1` opts into live bibliographic checks |
| Risk-stratified claim, scope, and novelty checks | Vendored workflow prompts and schemas preserve high-impact-first sampling plus advisory-only scope and search-bounded novelty rows |
| Executable panel/degradation/pipeline-boundary checks | Vendored with their hermetic tests and exposed by the optional full-runtime manifest |
| SessionStart and SubagentStop hooks, including the update reminder | Vendored for traceability only; Codex does not install or execute Claude hooks |
| Plugin marketplace update | Refresh with `codex plugin marketplace upgrade ars-codex`, then re-add `ars-codex@ars-codex`; direct skill installs still reinstall or pull |
| Claude Code Agent Team | Not automatic; Codex subagents require an explicit user request for delegation or parallel agents |
| Cross-model provider dispatch from upstream docs | Disabled by default; available only with explicit provider configuration and explicit user consent |

### Optional External Cross-Model Reviewer API

For reviewer calibration or cross-model devil's advocate checks, configure one
of the provider tuples documented in
`ars/shared/cross_model_verification.md`, then ask for cross-model verification
explicitly in the prompt. For example:

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export ARS_CROSS_MODEL="gpt-5.5"
```

Without both a configured provider and explicit user consent for the content
class being sent, ARS-Codex falls back to single-runtime review and reports that
cross-model verification was unavailable.

## Support And Sponsorship

If ARS-Codex helps your research workflow, you can support maintenance through
[Buy Me a Coffee](https://buymeacoffee.com/crucify020v).

## Security

Do not open public issues for vulnerabilities. Follow
[`SECURITY.md`](SECURITY.md) for private reporting, and see the
[release readiness and security report](security_best_practices_report.md) for
the latest local validation summary.

### File Layout For Advanced Use

The entry point is:

```text
skills/academic-research-suite/SKILL.md
```

Workflow content is under:

```text
skills/academic-research-suite/ars/<workflow>/
```

Shared schemas, compliance rules, and cross-workflow contracts are under:

```text
skills/academic-research-suite/ars/shared/
```

When debugging or updating the package, preserve these paths. Many ARS workflow
files cross-reference `shared/`, `scripts/`, `examples/`, and other workflow
directories.

## Update Policy

Updates sync selected upstream ARS content into `skills/academic-research-suite/ars/`.
Do not mirror the Claude Code repo blindly; exclude Claude/plugin loader files
such as `.claude/`, `.claude-plugin/`, source `.gitignore`, and symlink-only
alias directories that are not needed in Codex. Nested upstream `.github/`
workflows may be retained as inactive traceability and self-test fixtures.

### Inactive Upstream Scripts

Some upstream maintenance scripts are vendored but intentionally inactive in
this Codex package because they require non-vendored Claude Code inputs such as
`.claude/CLAUDE.md`. See `inactive_upstream_scripts` in
`skills/academic-research-suite/manifest.json` before wiring any upstream script
into Codex CI.

## Contributors And Acknowledgements

**Cheng-I Wu** - Maintainer of the ARS suite and this Codex sibling
distribution.

**Codex** - Assisted with the Codex adapter packaging, router-policy hardening,
test fixes, and release-readiness review under maintainer direction.

**[vinschger](https://github.com/vinschger)** - Reported beginner installation
friction around `python` vs `python3`, which led to clearer setup instructions
for macOS and other environments.

**[Joker2377](https://github.com/Joker2377)** - Helped answer community
installation questions and clarify beginner setup steps in issue discussions.

Vendored upstream ARS contributors are acknowledged in
[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors).
