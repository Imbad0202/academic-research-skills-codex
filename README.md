# Academic Research Skills for Codex

Codex-native packaging of the Academic Research Skills suite.

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

This Codex package is version `0.1.1`. The repo-root `VERSION` file,
`skills/academic-research-suite/SKILL.md` metadata version, and
`skills/academic-research-suite/manifest.json` `adapter_version` track the
Codex package version independently of the vendored ARS suite. Vendored upstream
versions are recorded by commit in `manifest.source_repositories[]`.

## Install

Install the skill from this repo path:

```bash
python /Users/imbad/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo Imbad0202/academic-research-skills-codex \
  --path skills/academic-research-suite
```

Restart Codex after installation.

## Usage

Invoke the suite explicitly with `$academic-research-suite`, then describe the
research task and provide any source files, notes, draft text, reviewer comments,
or output constraints.

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

### Working Pattern

For best results, start with the workflow goal and the current state of your
materials:

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: Traditional Chinese, APA 7, higher education policy audience.
```

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

### Codex Adapter Behavior

ARS was originally written for Claude Code. In this Codex package:

- The vendored `agents/*.md` files are used as role and phase prompts.
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

### Optional Claude Opus 4.7 Reviewer API

For reviewer calibration or cross-model devil's advocate checks:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export ARS_CROSS_MODEL="claude-opus-4.7"
```

Then ask for cross-model verification explicitly in the prompt. Without both
environment variables, ARS Codex falls back to single-runtime review and should
report that the Claude Opus 4.7 verifier was unavailable.

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

Updates are manual cherry-picks from upstream ARS. Do not mirror the Claude Code
repo blindly; review path references and Claude-specific runtime language before
updating this Codex package.

### Inactive Upstream Scripts

Some upstream maintenance scripts are vendored but intentionally inactive in
this Codex package because they require non-vendored Claude Code inputs such as
`.claude/CLAUDE.md`. See `inactive_upstream_scripts` in
`skills/academic-research-suite/manifest.json` before wiring any upstream script
into Codex CI.
