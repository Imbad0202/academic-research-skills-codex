# ARS Codex Setup

This document describes the Codex package
`academic-research-skills-codex`. It is not the Claude Code plugin setup guide.
For the native Claude Code version, use
`Imbad0202/academic-research-skills`.

## Minimum Viable Setup

Install the single Codex skill. Use `--method git` so public and credentialed
GitHub access both behave consistently:

```bash
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

To update an existing install:

```bash
rm -rf "$HOME/.codex/skills/academic-research-suite"
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

Open a new Codex conversation after installation. Existing sessions may keep
their old skill cache; do not close unrelated Claude or Codex sessions just to
pick up this skill.

Then invoke the suite explicitly:

```text
Use $academic-research-suite to plan a systematic literature review on AI in higher education QA.
```

The skill name is singular: `$academic-research-suite`.

Verify the install with `/skills`. You should see one ARS entry only:
`academic-research-suite` or `Academic Research ...`. If you see separate
`academic-paper`, `academic-pipeline`, `deep-research`, or
`academic-paper-reviewer` entries from this package, reinstall with the update
command above and open a new Codex conversation.

No Anthropic API key is required for normal Codex use. The active Codex runtime
supplies the primary model. Optional Anthropic configuration is only for the
extra cross-model reviewer described below.

## Claude-Style Aliases

Claude Code ARS installs `/ars-*` slash commands. Codex does not expose the
same command registry, so this package emulates their intent through the
`$academic-research-suite` router.

Use the plain alias when slash input is intercepted by the client:

```text
ars-plan my paper on AI governance in universities
ars-revision-coach reviewer_comments.md
ars-full topic: demographic decline and university quality assurance
```

You can also wrap the alias inside the explicit skill invocation:

```text
Use $academic-research-suite: ars-outline for this manuscript draft.
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

The `model: opus` / `model: sonnet` fields in `commands/ars-*.md` are Claude
Code routing metadata. Codex uses the active model unless the user explicitly
requests a different model in the conversation.

## Socratic Scoping For Vague Paper Topics

When the user says they want to write a paper but only has a topic, tentative
title, or broad direction, the Codex router should follow upstream ARS behavior:
start with `deep-research` `socratic` mode before outline, drafting, or full
pipeline execution.

Use this prompt shape:

```text
Use $academic-research-suite.
I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic questioning to narrow the research question first.
Do not produce an outline yet.
```

Expected behavior:

- route to `deep-research` `socratic` mode
- ask narrowing questions first
- produce 2-3 candidate RQs only after the dialogue has enough constraints
- do not start `academic-paper` outline/drafting until the RQ is clear

For a full pipeline with Socratic Stage 1, say:

```text
Use $academic-research-suite to start academic-pipeline.
Stage 1 must begin with deep-research socratic mode because I only have a broad topic.
Stop after the RQ Brief and pipeline dashboard.
```

## Smoke Tests

Codex app / interactive CLI:

```text
/skills
```

Expected: one ARS entry only.

Router smoke:

```text
Use $academic-research-suite.
I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
```

Expected: `deep-research` `socratic` mode.

Codex CLI:

```bash
codex exec --ephemeral --sandbox read-only \
  -C /path/to/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: I want to write a paper on AI adoption in higher education quality assurance, but I do not yet have a clear research question. According to the academic-research-suite router, classify the workflow and mode.'
```

## Non-Blocking Codex Warnings

These messages do not mean ARS failed to install:

- `[features].codex_hooks is deprecated`: update your Codex config when
  convenient. ARS Codex does not require hooks for normal use.
- `hooks need review before they can run`: review those hooks separately if you
  use them. Vendored Claude hooks in this package are traceability metadata and
  are not installed or executed by Codex.

## Optional Local Tools

Markdown output works without extra tools. Install the following only when you
need deterministic local conversions or corpus adapters.

### DOCX Output

Direct `.docx` generation uses Pandoc. If Pandoc is unavailable, ARS Codex
should provide Markdown plus conversion instructions.

```bash
# macOS
brew install pandoc

# Linux (Debian/Ubuntu)
sudo apt-get install pandoc
```

### LaTeX / PDF Output

PDF output requires `tectonic` and the relevant fonts. This is optional.

```bash
# macOS
brew install tectonic

# Linux (Debian/Ubuntu)
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
```

Recommended fonts for APA 7 CJK output:

- Times New Roman
- Source Han Serif TC VF / Noto Serif TC
- Courier New

### Adapter Dependencies

The reference Material Passport adapters use Python packages from the vendored
`requirements-dev.txt`:

```bash
cd skills/academic-research-suite/ars
python -m pip install -r requirements-dev.txt
```

## Material Passport `literature_corpus[]` Adapters

If you maintain a curated literature corpus, run adapters before the ARS session
and pass the resulting `passport.yaml` into Codex.

From the vendored ARS root:

```bash
cd skills/academic-research-suite/ars

python scripts/adapters/folder_scan.py \
  --input /path/to/pdfs \
  --passport passport.yaml \
  --rejection-log rejection_log.yaml

python scripts/adapters/zotero.py \
  --input my-zotero-export.json \
  --passport passport.yaml \
  --rejection-log rejection_log.yaml

python scripts/adapters/obsidian.py \
  --input ~/Obsidian/Lit\ Notes \
  --passport passport.yaml \
  --rejection-log rejection_log.yaml
```

The consumer protocol is unchanged from upstream ARS: `bibliography_agent`
and `literature_strategist_agent` use corpus-first / search-fills-gap behavior
when a non-empty corpus is present and parses cleanly. See
[`academic-pipeline/references/literature_corpus_consumers.md`](../academic-pipeline/references/literature_corpus_consumers.md).

## Optional Environment Flags

All flags are opt-in.

| Flag | Codex behavior |
|---|---|
| `ARS_SOCRATIC_READING_PROBE=1` | Enables the Socratic reading-check probe in `socratic_mentor_agent` when the workflow reaches that prompt. |
| `ARS_PASSPORT_RESET=1` | Promotes FULL checkpoints to Material Passport reset boundaries. A "fresh Claude Code session" in upstream wording means a new Codex conversation here. |
| `ARS_CLAIM_AUDIT=1` | Enables the optional v3.8 claim-reference alignment audit gate when the workflow reaches that upstream path. |
| `ARS_CROSS_MODEL=claude-opus-4.7` + `ANTHROPIC_API_KEY` | Enables the optional external Claude Opus reviewer when explicitly requested by the user. |
| `ARS_CROSS_MODEL_SAMPLE_INTERVAL` | Advisory sampling interval for cross-model checks when cross-model review is explicitly enabled. |
| `S2_API_KEY` | Optional Semantic Scholar key for faster reference lookups and contamination-signal migration. |
| `OPENALEX_POLITE_EMAIL`, `CROSSREF_POLITE_EMAIL` | Optional polite-pool identifiers for ARS v3.9.0 OpenAlex / Crossref triangulation clients. |

Upstream GPT/Gemini cross-model examples are not active in this Codex package.
Do not set `OPENAI_API_KEY` or `GOOGLE_AI_API_KEY` for ARS Codex cross-model
review; Codex itself already supplies the primary OpenAI model.

## Claude Code Features That Do Not Copy Directly

| Claude Code feature | Codex status |
|---|---|
| `/plugin marketplace add` / `/plugin install` | Not available. Install this repo as a Codex skill. |
| Native `/ars-*` slash-command registration | Not available. Use `ars-*` aliases through `$academic-research-suite`. |
| `skills/` symlink auto-discovery | Replaced by one Codex router skill. |
| `agents/` plugin-shipped agents | Used as role prompts inline; no automatic dispatch. |
| Claude Code Agent Team / Task tool | Codex subagents require an explicit user request for delegation or parallel work. |
| SessionStart / SubagentStop hooks | Vendored for traceability only; not installed or executed by Codex. |
| `model: opus` / `model: sonnet` command routing | Ignored as routing control; Codex uses the active model. |
| Plugin auto-update | Not available; update by reinstalling or pulling the Codex repo. |

## Development Validation

Run these from the Codex repo root:

```bash
python -m json.tool skills/academic-research-suite/manifest.json
python skills/academic-research-suite/ars/scripts/check_data_access_level.py --path skills/academic-research-suite/ars
python skills/academic-research-suite/ars/scripts/check_task_type.py --path skills/academic-research-suite/ars
```

Run upstream pytest suites from the vendored ARS root because the tests import
`scripts.*`:

```bash
cd skills/academic-research-suite/ars
python -m pytest --tb=short -q
```

The Codex package patches nested path lookup where practical. For first-time
vendoring before this repository's Git history contains the upstream v3.6.7
manifest, `scripts/check_v3_6_8_pattern_protection.py` falls back to
`scripts/codex_v3_6_7_block_baseline.json` so byte-equivalence checks still
detect protected-block mutations instead of self-baselining.
