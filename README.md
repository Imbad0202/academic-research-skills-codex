# Academic Research Skills for Codex

[![Version](https://img.shields.io/badge/version-v0.1.6-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

Codex-native packaging of the Academic Research Skills suite. This is the
sibling Codex distribution of
[Academic Research Skills for Claude Code](https://github.com/Imbad0202/academic-research-skills).

This repository vendors the ARS workflow content as a single Codex skill:

```text
skills/academic-research-suite/
  SKILL.md
  manifest.json
  agents/openai.yaml
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

## Claude Code Version

This repository is the Codex package. For the original Claude Code version of
Academic Research Skills, use
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills).

Use the Claude Code repo when you want the native Claude Code skill layout,
Claude-specific agent-team behavior, or the original ARS development history.
Use this repo when you want the Codex-native single-suite skill.

## Versioning

This Codex package is version `0.1.6`. The repo-root `VERSION` file,
`skills/academic-research-suite/SKILL.md` metadata version, and
`skills/academic-research-suite/manifest.json` `adapter_version` track the
Codex package version independently of the vendored ARS suite. Vendored upstream
versions are recorded by commit in `manifest.source_repositories[]`.

The vendored ARS source currently tracks
`Imbad0202/academic-research-skills@1d0c8625207c9cd8fc46132b1ef930f2cc012236`.

## Install Or Update

Install the skill from this repo path. Use `--method git` so public and
credentialed GitHub access both work consistently:

```bash
python /Users/imbad/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

To update an existing install:

```bash
rm -rf /Users/imbad/.codex/skills/academic-research-suite
python /Users/imbad/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

Open a new Codex conversation after installation. Existing Codex sessions may
keep their old skill cache; you do not need to close unrelated Claude or Codex
sessions.

Verify with `/skills`: you should see one ARS entry, `academic-research-suite`
or `Academic Research ...`. You should **not** see separate `academic-paper`,
`academic-pipeline`, `deep-research`, or `academic-paper-reviewer` skills from
this package. If you do, reinstall with the update command above and open a new
Codex conversation.

## Codex Docs

- [Codex setup](skills/academic-research-suite/ars/docs/SETUP.md) covers
  installation, `ars-*` aliases, optional tools, Material Passport adapters,
  and unsupported Claude plugin features.
- [Codex architecture](skills/academic-research-suite/ars/docs/ARCHITECTURE.md)
  explains the logical ARS pipeline with the Codex runtime overlay.

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
  -C /Users/imbad/Projects/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: I want to write a paper on AI adoption in higher education quality assurance, but I do not yet have a clear research question. According to the academic-research-suite router, classify the workflow and mode.'
```

### Non-Blocking Codex Warnings

These Codex messages do not mean ARS failed to install:

- `[features].codex_hooks is deprecated` — update your Codex config when
  convenient; ARS Codex does not require hooks for normal use.
- `hooks need review before they can run` — review those hooks separately if
  you use them. ARS Codex treats vendored Claude hooks as traceability metadata
  and does not require them.

### Codex Adapter Behavior

ARS was originally written for Claude Code. In this Codex package:

- The vendored `agents/*.md` files are used as role and phase prompts.
- The vendored `commands/ars-*.md` files are prompt recipes only. Codex does not
  register them as slash commands.
- The vendored `hooks/hooks.json` file is preserved for upstream traceability
  only. Codex does not install Claude Code hooks from this package.
- Codex does not automatically spawn background agents unless you explicitly ask
  for delegated or parallel agent work.
- Web/source verification uses Codex browsing and must cite sources when current
  or external facts matter.
- Cross-model verification is disabled by default. When explicitly requested in
  this Codex package, configure `ARS_CROSS_MODEL=claude-opus-4.7` and
  `ANTHROPIC_API_KEY`; the external reviewer uses Anthropic Claude Opus 4.7 API,
  not Codex/OpenAI API. Upstream GPT/Gemini secondary-dispatch instructions are
  ignored unless this explicit Anthropic configuration is present.
- Upstream references to a "fresh Claude Code session" mean a new Codex
  conversation in this package; Material Passport reset semantics still apply.
- If a citation, source, statistic, or journal policy cannot be verified, Codex
  should mark it as unverified rather than invent support.

### Claude v3.7 Parity

This package aims for the same user-facing workflow shape as the Claude Code
v3.7 plugin where Codex has an equivalent concept.

| Claude v3.7 feature | Codex package behavior |
|---|---|
| One installable plugin | One installable Codex skill at `skills/academic-research-suite` |
| `/ars-*` slash commands | Emulated as `ars-*` aliases through the skill router; not native slash commands |
| Four upstream skills auto-discovered from `skills/` symlinks | Single Codex router skill selects the workflow and reads the vendored workflow `WORKFLOW.md` files |
| Plugin-shipped agents | Agent files are role/phase prompts; Codex runs them inline unless the user explicitly asks for delegated subagents |
| `model: opus` / `model: sonnet` command routing | Treated as Claude metadata; Codex uses the active model |
| SessionStart and SubagentStop hooks | Vendored for traceability only; Codex does not install or execute Claude hooks |
| Plugin marketplace update / auto-update | Not available here; update by reinstalling or pulling this Codex repo |
| Claude Code Agent Team | Not automatic; Codex subagents require an explicit user request for delegation or parallel agents |
| Cross-model GPT/Gemini dispatch from upstream docs | Disabled; Codex package only supports optional Anthropic Claude Opus 4.7 review when explicitly configured |

### Optional Claude Opus 4.7 Reviewer API

For reviewer calibration or cross-model devil's advocate checks:

```bash
export ANTHROPIC_API_KEY="<your-anthropic-api-key>"
export ARS_CROSS_MODEL="claude-opus-4.7"
```

Then ask for cross-model verification explicitly in the prompt. Without both
environment variables, ARS Codex falls back to single-runtime review and should
report that the Claude Opus 4.7 verifier was unavailable.

## Support And Sponsorship

If ARS Codex helps your research workflow, you can support maintenance through
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
such as `.claude/`, `.claude-plugin/`, `.github/`, source `.gitignore`, and
symlink-only alias directories that are not needed in Codex.

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

Vendored upstream ARS contributors are acknowledged in
[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors).
